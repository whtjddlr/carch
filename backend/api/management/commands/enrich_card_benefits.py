import json
import re
import sqlite3
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand


NON_EMPTY_JSON_SQL = "is not null and trim({column}) not in ('', '[]', '{{}}', 'null')"


class VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style', 'noscript', 'svg'}:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in {'script', 'style', 'noscript', 'svg'} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth:
            return
        text = re.sub(r'\s+', ' ', data or '').strip()
        if text:
            self.parts.append(text)

    def text(self):
        return re.sub(r'\s+', ' ', ' '.join(self.parts)).strip()


def json_loads(value, fallback=None):
    if fallback is None:
        fallback = []
    if value in (None, '', 'null'):
        return fallback
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback
    return parsed if parsed is not None else fallback


def amount_to_krw(raw, unit):
    amount = float(raw)
    if unit == '억':
        amount *= 100_000_000
    elif unit == '천만':
        amount *= 10_000_000
    elif unit == '백만':
        amount *= 1_000_000
    elif unit == '만':
        amount *= 10_000
    elif unit == '천':
        amount *= 1_000
    return int(round(amount))


def unique_sorted(values):
    return sorted({int(value) for value in values if int(value) > 0})


def extract_amounts(patterns, text):
    values = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            values.append(amount_to_krw(match.group('amount'), match.groupdict().get('unit') or ''))
    return unique_sorted(values)


def extract_rule_hints(text):
    compact = re.sub(r'\s+', ' ', text or '')
    amount = r'(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>억|천만|백만|만|천)?\s*원'
    return {
        'requiredPreviousMonthSpendKrw': extract_amounts(
            [
                rf'(?:전월|지난달|직전\s*1개월).{{0,45}}?{amount}.{{0,25}}?(?:이상|충족|실적)',
                rf'(?:이용실적|전월실적).{{0,45}}?{amount}',
            ],
            compact,
        ),
        'monthlyBenefitLimitKrw': extract_amounts(
            [
                rf'(?:월|매월|통합).{{0,35}}?(?:한도|최대|까지).{{0,20}}?{amount}',
                rf'{amount}.{{0,20}}?(?:월|매월|통합).{{0,35}}?(?:한도|최대|까지)',
            ],
            compact,
        ),
        'minPaymentAmountKrw': extract_amounts(
            [
                rf'(?:건당|1회|결제금액|이용금액).{{0,35}}?{amount}.{{0,20}}?(?:이상|초과)',
                rf'{amount}.{{0,20}}?(?:이상|초과).{{0,20}}?(?:결제|이용|건당)',
            ],
            compact,
        ),
        'perTransactionLimitKrw': extract_amounts(
            [
                rf'(?:건당|1회).{{0,35}}?(?:한도|최대|까지).{{0,20}}?{amount}',
                rf'{amount}.{{0,20}}?(?:건당|1회).{{0,35}}?(?:한도|최대|까지)',
            ],
            compact,
        ),
        'hasSharedMonthlyLimitEvidence': bool(re.search(r'(?:통합\s*한도|월\s*통합|통합\s*월)', compact)),
        'hasPerformanceExclusionEvidence': bool(re.search(r'(?:전월\s*실적\s*제외|실적\s*산정\s*제외|이용실적\s*제외)', compact)),
        'hasInstallmentBenefitExclusionEvidence': bool(
            re.search(r'(?:할부|분할납부).{0,35}(?:혜택|할인|적립).{0,20}(?:제외|미적용|불가)', compact)
            or re.search(r'(?:혜택|할인|적립).{0,35}(?:할부|분할납부).{0,20}(?:제외|미적용|불가)', compact)
        ),
        'hasInterestFreeInstallmentExclusionEvidence': bool(
            re.search(r'(?:무이자|부분무이자).{0,35}(?:할부)?.{0,20}(?:제외|미적용|불가)', compact)
            or re.search(r'(?:제외|미적용|불가).{0,35}(?:무이자|부분무이자)', compact)
        ),
    }


def fetch_visible_text(url, timeout):
    safe_url = quote(url, safe=':/?&=#%')
    request = Request(
        safe_url,
        headers={
            'User-Agent': 'Mozilla/5.0 CarchBenefitEnricher/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read(1_500_000)
        content_type = response.headers.get('content-type') or ''
    if 'pdf' in content_type.lower() or raw[:4] == b'%PDF':
        return '', 'pdf'
    encoding = 'utf-8'
    match = re.search(r'charset=([\w-]+)', content_type, re.I)
    if match:
        encoding = match.group(1)
    html = raw.decode(encoding, errors='replace')
    parser = VisibleTextParser()
    parser.feed(html)
    return parser.text(), content_type


def card_coverage(row):
    benefit_count = int(row['benefit_count'] or 0)
    if not benefit_count:
        return 0
    weighted = (
        int(row['has_value'] or 0) * 2
        + int(row['has_required'] or 0) * 2
        + int(row['has_monthly_limit'] or 0) * 2
        + int(row['has_min_payment'] or 0)
        + int(row['has_merchants'] or 0)
        + int(row['has_exclusions'] or 0)
        + int(row['auto_usable'] or 0) * 2
    )
    max_score = benefit_count * 11
    return round(weighted / max_score, 3)


def card_row_to_dict(row):
    data = dict(row)
    data['coverageScore'] = card_coverage(row)
    data['manualReviewRatio'] = round((data['manual_review'] or 0) / max(data['benefit_count'] or 1, 1), 3)
    return data


class Command(BaseCommand):
    help = 'Inspect card benefit rule coverage and optionally extract official-page enrichment hints.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=20)
        parser.add_argument('--card-id', action='append', default=[])
        parser.add_argument('--fetch-official', action='store_true')
        parser.add_argument('--timeout', type=int, default=8)
        parser.add_argument('--write', action='store_true')
        parser.add_argument(
            '--output',
            default=str(settings.BASE_DIR / 'data' / 'card_benefit_enrichment_report.json'),
        )

    def handle(self, *args, **options):
        card_ids = [str(value).strip() for value in options['card_id'] if str(value).strip()]
        limit = max(int(options['limit'] or 20), 1)
        report = self.build_report(card_ids=card_ids, limit=limit)

        if options['fetch_official']:
            self.attach_official_hints(report, limit=limit, timeout=options['timeout'])

        output = json.dumps(report, ensure_ascii=False, indent=2)
        if options['write']:
            output_path = Path(options['output'])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output, encoding='utf-8')
            self.stdout.write(self.style.SUCCESS(f'Wrote {output_path}'))
        else:
            self.stdout.write(output)

    def build_report(self, card_ids, limit):
        where = ''
        params = []
        if card_ids:
            placeholders = ','.join('?' for _ in card_ids)
            where = f'where c.card_ad_id in ({placeholders})'
            params.extend(card_ids)

        query = f'''
            select c.card_ad_id, c.card_name, c.issuer_name, c.official_url, c.naver_url,
                   count(b.benefit_id) as benefit_count,
                   sum(case when b.rate_percent is not null or b.amount_krw is not null then 1 else 0 end) as has_value,
                   sum(case when b.required_previous_month_spend_krw is not null then 1 else 0 end) as has_required,
                   sum(case when b.min_payment_amount_krw is not null then 1 else 0 end) as has_min_payment,
                   sum(case when b.monthly_benefit_limit_krw is not null then 1 else 0 end) as has_monthly_limit,
                   sum(case when b.target_merchants_json {NON_EMPTY_JSON_SQL.format(column='b.target_merchants_json')} then 1 else 0 end) as has_merchants,
                   sum(case when b.exclusion_keywords_json {NON_EMPTY_JSON_SQL.format(column='b.exclusion_keywords_json')} then 1 else 0 end) as has_exclusions,
                   sum(case when b.has_shared_monthly_limit = 1 then 1 else 0 end) as has_shared,
                   sum(case when b.is_auto_usable = 1 then 1 else 0 end) as auto_usable,
                   sum(case when b.needs_manual_review = 1 then 1 else 0 end) as manual_review
            from cards c
            left join card_benefits b on b.card_ad_id = c.card_ad_id
            {where}
            group by c.card_ad_id
            having benefit_count > 0
        '''

        with sqlite3.connect(settings.CARD_MASTER_DB) as connection:
            connection.row_factory = sqlite3.Row
            rows = [card_row_to_dict(row) for row in connection.execute(query, params).fetchall()]
            summary = self.coverage_summary(connection)
            demo_pool = [
                row for row in rows
                if row['manualReviewRatio'] <= 0.4
                and row['has_value'] > 0
                and row['has_required'] > 0
                and row['has_monthly_limit'] > 0
            ] or rows
            demo_cards = sorted(
                demo_pool,
                key=lambda row: (
                    row['coverageScore'],
                    -row['manualReviewRatio'],
                    row['has_monthly_limit'],
                    row['has_merchants'],
                    row['auto_usable'],
                ),
                reverse=True,
            )[:limit]
            enrichment_targets = sorted(
                rows,
                key=lambda row: (
                    row['has_monthly_limit'] == 0,
                    row['has_min_payment'] == 0,
                    row['has_merchants'] == 0,
                    row['manualReviewRatio'],
                    row['benefit_count'],
                ),
                reverse=True,
            )[:limit]

        return {
            'generatedAt': datetime.now().isoformat(timespec='seconds'),
            'cardMasterDb': str(settings.CARD_MASTER_DB),
            'summary': summary,
            'demoCandidateCriteria': [
                '카테고리/할인값/전월실적/월한도 필드가 많이 채워진 카드',
                '자동 계산 가능 행이 많고 수동 검수 비율이 낮은 카드',
                '남주현 시나리오는 이 후보 중 소비 패턴과 맞는 카드만 사용',
            ],
            'demoCandidates': demo_cards,
            'enrichmentTargets': enrichment_targets,
        }

    def coverage_summary(self, connection):
        total = connection.execute('select count(*) from card_benefits').fetchone()[0]
        fields = [
            'rate_percent',
            'amount_krw',
            'required_previous_month_spend_krw',
            'min_payment_amount_krw',
            'monthly_benefit_limit_krw',
            'target_merchants_json',
            'exclusion_keywords_json',
        ]
        coverage = {}
        for field in fields:
            if field.endswith('_json'):
                sql = f"select count(*) from card_benefits where {field} {NON_EMPTY_JSON_SQL.format(column=field)}"
            else:
                sql = f'select count(*) from card_benefits where {field} is not null'
            count = connection.execute(sql).fetchone()[0]
            coverage[field] = {'count': count, 'ratio': round(count / max(total, 1), 3)}
        return {'benefitRows': total, 'fieldCoverage': coverage}

    def attach_official_hints(self, report, limit, timeout):
        targets = report['enrichmentTargets'][:limit]
        for card in targets:
            url = card.get('official_url') or card.get('officialUrl')
            if not url:
                card['officialFetch'] = {'ok': False, 'error': 'missing official_url'}
                continue
            try:
                text, content_type = fetch_visible_text(url, timeout=timeout)
            except (HTTPError, URLError, TimeoutError, OSError, UnicodeError) as exc:
                card['officialFetch'] = {'ok': False, 'error': str(exc)}
                continue
            hints = extract_rule_hints(text)
            card['officialFetch'] = {
                'ok': bool(text),
                'contentType': content_type,
                'textLength': len(text),
                'hints': hints,
                'manualReviewRecommended': self.needs_manual_review(card, hints),
            }

    def needs_manual_review(self, card, hints):
        if not hints:
            return True
        if card.get('has_monthly_limit', 0) == 0 and not hints.get('monthlyBenefitLimitKrw'):
            return True
        if card.get('has_min_payment', 0) == 0 and not hints.get('minPaymentAmountKrw'):
            return True
        if card.get('manualReviewRatio', 0) >= 0.4:
            return True
        return False
