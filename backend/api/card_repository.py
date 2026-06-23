import sqlite3
from pathlib import Path

from django.conf import settings


CURATED_CARD_COPY = {
    10029: {
        'benefitSummary': '언제나 1.5% 할인',
        'benefits': ['언제나 1.5% 할인', '주유소 최대 1% 할인', '대중교통 최대 1% 할인'],
    },
    10612: {
        'benefitSummary': '쇼핑 최대 15% 할인',
        'benefits': ['온라인 쇼핑 10% 할인', '오프라인 쇼핑 10% 할인', '쇼핑멤버십 50% 할인'],
    },
    10609: {
        'benefitSummary': '이마트 계열 15% 할인',
        'benefits': ['이마트 계열 15% 할인', '국내외 가맹점 0.5% 적립', '전월 실적 40만원'],
    },
}


def connect_card_db():
    connection = sqlite3.connect(settings.CARD_MASTER_DB)
    connection.row_factory = sqlite3.Row
    return connection


def image_filename_for(card_ad_id, local_path=''):
    candidates = []
    if local_path:
        candidates.append(Path(local_path).name)
    candidates.extend([f'{card_ad_id}.png', f'{card_ad_id}.jpg', f'{card_ad_id}.jpeg', f'{card_ad_id}.gif'])

    for filename in candidates:
        if filename and (settings.CARD_IMAGE_DIR / filename).exists():
            return filename
    return None


def card_image_url(request, card_ad_id, local_path=''):
    filename = image_filename_for(card_ad_id, local_path)
    if not filename:
        return ''
    return request.build_absolute_uri(f'/api/card-images/{filename}')


def benefit_label(row):
    scope = row['scope_name'] or '혜택'
    unit = row['benefit_unit']
    value = row['benefit_value']
    amount = row['amount_krw']

    if row['rate_percent'] is not None:
        return f'{scope} {row["rate_percent"]:g}%'
    if amount is not None:
        return f'{scope} {int(amount):,}원'
    if value is not None and unit == 'percent':
        return f'{scope} {value:g}%'
    return scope


def list_benefits(card_ad_id, limit=5):
    with connect_card_db() as connection:
        rows = connection.execute(
            '''
            select benefit_type, scope_name, benefit_value, benefit_unit, rate_percent, amount_krw,
                   required_previous_month_spend_krw, monthly_benefit_limit_krw, calculation_status
            from card_benefits
            where card_ad_id = ?
            order by
              case when is_auto_usable = 1 then 0 else 1 end,
              case benefit_type
                when 'discount_rate' then 0
                when 'point_rate' then 1
                when 'discount' then 2
                else 3
              end,
              scope_name
            limit ?
            ''',
            (card_ad_id, limit),
        ).fetchall()

    benefits = []
    seen = set()
    for row in rows:
        label = benefit_label(row)
        if label in seen:
            continue
        seen.add(label)
        benefits.append(
            {
                'type': row['benefit_type'],
                'scope': row['scope_name'],
                'label': label,
                'ratePercent': row['rate_percent'],
                'amountKrw': row['amount_krw'],
                'requiredPreviousMonthSpendKrw': row['required_previous_month_spend_krw'],
                'monthlyBenefitLimitKrw': row['monthly_benefit_limit_krw'],
                'calculationStatus': row['calculation_status'],
            }
        )
    return benefits


def serialize_card(row, request, include_benefits=False):
    card_ad_id = row['card_ad_id']
    benefits = list_benefits(card_ad_id, 6 if include_benefits else 3)
    benefit_labels = [benefit['label'] for benefit in benefits]
    curated = CURATED_CARD_COPY.get(card_ad_id, {})
    display_benefits = curated.get('benefits') or benefit_labels

    return {
        'id': str(card_ad_id),
        'cardAdId': card_ad_id,
        'card_ad_id': card_ad_id,
        'name': row['card_name'],
        'cardName': row['card_name'],
        'card_name': row['card_name'],
        'issuer': row['issuer_name'],
        'issuerName': row['issuer_name'],
        'issuer_name': row['issuer_name'],
        'issuerCode': row['issuer_code'],
        'issuer_code': row['issuer_code'],
        'titleDescription': row['title_description'],
        'title_description': row['title_description'],
        'benefitSummary': curated.get('benefitSummary') or (benefit_labels[0] if benefit_labels else row['title_description']),
        'benefits': display_benefits,
        'benefitItems': benefits if include_benefits else [],
        'annualFee': row['domestic_annual_fee'] or 0,
        'domesticAnnualFee': row['domestic_annual_fee'] or 0,
        'domestic_annual_fee': row['domestic_annual_fee'] or 0,
        'foreignAnnualFee': row['foreign_annual_fee'] or 0,
        'previousMonthMinSpend': row['previous_month_min_spend'],
        'previous_month_min_spend': row['previous_month_min_spend'],
        'issueStatus': row['issue_status'],
        'issue_status': row['issue_status'],
        'newIssueAvailable': row['new_issue_available'],
        'officialUrl': row['official_url'],
        'naverUrl': row['naver_url'],
        'imageUrl': card_image_url(request, card_ad_id, row['card_image_local_path']),
        'image_url': card_image_url(request, card_ad_id, row['card_image_local_path']),
    }


def fetch_cards(request, limit=30, search='', issuer='', active_only=False):
    clauses = ['card_image_status = ?']
    params = ['downloaded']
    if search:
        clauses.append('(card_name like ? or issuer_name like ? or title_description like ?)')
        keyword = f'%{search}%'
        params.extend([keyword, keyword, keyword])
    if issuer:
        clauses.append('issuer_name like ?')
        params.append(f'%{issuer}%')
    if active_only:
        clauses.append("issue_status = 'active'")

    where_sql = ' and '.join(clauses)
    params.append(limit)
    with connect_card_db() as connection:
        rows = connection.execute(
            f'''
            select *
            from cards
            where {where_sql}
            order by
              case when issue_status = 'active' then 0 else 1 end,
              card_ad_id desc
            limit ?
            ''',
            params,
        ).fetchall()
    return [serialize_card(row, request) for row in rows]


def fetch_card(card_ad_id, request):
    with connect_card_db() as connection:
        row = connection.execute('select * from cards where card_ad_id = ?', (card_ad_id,)).fetchone()
    if not row:
        return None
    return serialize_card(row, request, include_benefits=True)
