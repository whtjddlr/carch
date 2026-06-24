import json
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
    10106: {
        'benefitSummary': '카페·음식점 생활권 집중 할인',
        'benefits': ['카페 할인', '음식점 할인', '생활 영역 특화'],
    },
    10107: {
        'benefitSummary': '온라인 쇼핑·편의점 집중 할인',
        'benefits': ['온라인 쇼핑 할인', '편의점 할인', '생활 쇼핑 특화'],
    },
    10071: {
        'benefitSummary': '카페·생활 결제 특화 할인',
        'benefits': ['카페 할인', '생활 영역 할인', '전월 실적 40만원'],
    },
}
CURATED_VERIFIED_CARD_IDS = {10029, 10071, 10106, 10107, 10612}
CURATED_BENEFIT_EXCLUDED_SCOPES = {
    10106: {'쇼핑 멤버십'},
}
PREFERRED_CARD_IMAGES = {
}


def connect_card_db():
    connection = sqlite3.connect(settings.CARD_MASTER_DB)
    connection.row_factory = sqlite3.Row
    return connection


def image_filename_for(card_ad_id, local_path=''):
    preferred = PREFERRED_CARD_IMAGES.get(int(card_ad_id or 0))
    if preferred and (settings.CARD_IMAGE_DIR / preferred).exists():
        return preferred

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


def parse_json_value(value, fallback=None):
    if fallback is None:
        fallback = []
    if value in (None, '', 'null'):
        return fallback
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback
    return parsed if parsed is not None else fallback


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


def missing_rule_fields(benefit):
    missing = []
    if benefit['ratePercent'] is None and benefit['amountKrw'] is None and benefit['benefitValue'] is None:
        missing.append('benefitValue')
    if benefit['requiredPreviousMonthSpendKrw'] is None:
        missing.append('previousMonthSpend')
    if benefit['monthlyBenefitLimitKrw'] is None and not benefit['hasSharedMonthlyLimit']:
        missing.append('monthlyLimit')
    if not benefit['normalizedCategories']:
        missing.append('category')
    if not benefit['targetMerchants'] and benefit['calculationStatus'] in {'manual_review', 'conditional'}:
        missing.append('targetMerchants')
    return missing


def benefit_payment_rules(benefit):
    exclusion_keywords = benefit.get('exclusionKeywords') or []
    condition_lines = benefit.get('conditionLines') or []
    excluded_methods = set()

    for raw_keyword in exclusion_keywords:
        text = str(raw_keyword or '').replace(' ', '')
        if not text:
            continue
        if '무이자' in text:
            excluded_methods.add('interest_free_installment')
        elif '할부' in text:
            excluded_methods.add('installment')

    exclusion_markers = ('제외', '미적용', '불가', '제한', '대상아님', '대상아닌')
    for raw_line in condition_lines:
        text = str(raw_line or '').replace(' ', '')
        if not text or not any(marker in text for marker in exclusion_markers):
            continue
        if '무이자' in text:
            excluded_methods.add('interest_free_installment')
        elif '할부' in text:
            excluded_methods.add('installment')

    if 'installment' in excluded_methods:
        excluded_methods.add('interest_free_installment')

    return {
        'excludedPaymentMethods': sorted(excluded_methods),
        'paymentMethodRules': {
            'installmentBenefitEligible': 'installment' not in excluded_methods,
            'interestFreeInstallmentEligible': 'interest_free_installment' not in excluded_methods,
            'source': 'official_rule_text' if excluded_methods else 'not_detected',
        },
    }


def mark_benefit_review_state(benefit):
    missing = missing_rule_fields(benefit)
    verified = bool(benefit['isAutoUsable']) and not benefit['needsManualReview'] and not missing
    return {
        **benefit,
        'missingRuleFields': missing,
        'verified': verified,
        'manualInputAllowed': not verified,
    }


def benefit_data_status(benefits):
    if not benefits:
        return {
            'status': 'missing',
            'label': '혜택 데이터 없음',
            'manualInputAvailable': True,
            'missingRuleFields': ['benefits'],
        }

    missing_fields = sorted({field for benefit in benefits for field in benefit.get('missingRuleFields', [])})
    verified_count = sum(1 for benefit in benefits if benefit.get('verified'))
    if verified_count == len(benefits):
        status = 'verified'
        label = '검증 완료'
    elif verified_count:
        status = 'partial'
        label = '일부 보완 필요'
    else:
        status = 'needs_input'
        label = '정보 보완 필요'
    return {
        'status': status,
        'label': label,
        'manualInputAvailable': status != 'verified',
        'verifiedBenefitCount': verified_count,
        'totalBenefitCount': len(benefits),
        'missingRuleFields': missing_fields,
    }


def list_benefits(card_ad_id, limit=5):
    limit_clause = ''
    params = [card_ad_id]
    if limit is not None:
        limit_clause = 'limit ?'
        params.append(limit)

    with connect_card_db() as connection:
        rows = connection.execute(
            f'''
            select benefit_id, benefit_type, scope_name, benefit_value, benefit_unit, rate_percent, amount_krw,
                   required_previous_month_spend_krw, min_payment_amount_krw,
                   monthly_benefit_limit_krw, yearly_benefit_limit_krw,
                   categories_json, normalized_categories_json, target_merchants_json,
                   channel_flags_json, condition_lines_json, exclusion_keywords_json,
                   quality_score, needs_manual_review, has_shared_monthly_limit,
                   calculation_status, is_auto_usable, source_rule_ids_json
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
            {limit_clause}
            ''',
            params,
        ).fetchall()

    benefits = []
    seen = set()
    for row in rows:
        label = benefit_label(row)
        if label in seen:
            continue
        seen.add(label)
        benefit = {
            'id': row['benefit_id'],
            'benefitId': row['benefit_id'],
            'type': row['benefit_type'],
            'scope': row['scope_name'],
            'label': label,
            'benefitValue': row['benefit_value'],
            'benefitUnit': row['benefit_unit'],
            'ratePercent': row['rate_percent'],
            'amountKrw': row['amount_krw'],
            'requiredPreviousMonthSpendKrw': row['required_previous_month_spend_krw'],
            'minPaymentAmountKrw': row['min_payment_amount_krw'],
            'monthlyBenefitLimitKrw': row['monthly_benefit_limit_krw'],
            'yearlyBenefitLimitKrw': row['yearly_benefit_limit_krw'],
            'categories': parse_json_value(row['categories_json']),
            'normalizedCategories': parse_json_value(row['normalized_categories_json']),
            'targetMerchants': parse_json_value(row['target_merchants_json']),
            'channelFlags': parse_json_value(row['channel_flags_json'], {}),
            'conditionLines': parse_json_value(row['condition_lines_json']),
            'exclusionKeywords': parse_json_value(row['exclusion_keywords_json']),
            'qualityScore': row['quality_score'],
            'needsManualReview': bool(row['needs_manual_review']),
            'hasSharedMonthlyLimit': bool(row['has_shared_monthly_limit']),
            'calculationStatus': row['calculation_status'],
            'isAutoUsable': bool(row['is_auto_usable']),
            'sourceRuleIds': parse_json_value(row['source_rule_ids_json']),
        }
        benefit.update(benefit_payment_rules(benefit))
        benefits.append(mark_benefit_review_state(benefit))
    return benefits


def serialize_card(row, request, include_benefits=False):
    card_ad_id = row['card_ad_id']
    excluded_scopes = CURATED_BENEFIT_EXCLUDED_SCOPES.get(card_ad_id, set())
    benefits = [
        benefit
        for benefit in list_benefits(card_ad_id, 6 if include_benefits else 3)
        if benefit.get('scope') not in excluded_scopes
    ]
    status_benefits = [
        benefit
        for benefit in (list_benefits(card_ad_id, None) if include_benefits else benefits)
        if benefit.get('scope') not in excluded_scopes
    ]
    status = benefit_data_status(status_benefits)
    if card_ad_id in CURATED_VERIFIED_CARD_IDS and status_benefits:
        status = {
            **status,
            'status': 'verified',
            'label': '검증 완료',
            'manualInputAvailable': False,
            'verifiedBenefitCount': len(status_benefits),
            'totalBenefitCount': len(status_benefits),
            'missingRuleFields': [],
        }
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
        'benefitDataStatus': status,
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
