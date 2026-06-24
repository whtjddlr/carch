import json

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings

from .views import (
    _build_routing_suggestions,
    _benefit_rate_for_category,
    _estimate_card_value,
    _estimate_category_benefit,
    _recommendation_reason,
    normalize_plan_items,
)


class CardRecommendationLogicTests(SimpleTestCase):
    def test_category_specific_merchant_is_not_general_benefit(self):
        card = {
            'benefitItems': [
                {
                    'type': 'discount_rate',
                    'scope': '전통시장 대상 가맹점',
                    'label': '전통시장 대상 가맹점 7%',
                    'ratePercent': 7,
                }
            ]
        }

        rate, limit, label = _benefit_rate_for_category(card, '헬스')

        self.assertEqual(rate, 0.0)
        self.assertIsNone(limit)
        self.assertEqual(label, '해당 카테고리 혜택 없음')

    def test_structured_benefit_match_uses_category_rate(self):
        card = {
            'benefitItems': [
                {
                    'type': 'discount_rate',
                    'scope': '올리브영 등 오프라인샵',
                    'label': '올리브영 등 오프라인샵 7%',
                    'ratePercent': 7,
                }
            ]
        }

        rate, _, label = _benefit_rate_for_category(card, '뷰티')

        self.assertEqual(rate, 7)
        self.assertEqual(label, '올리브영 등 오프라인샵 7%')

    def test_interest_free_installment_exclusion_blocks_benefit(self):
        card = {
            'benefitItems': [
                {
                    'type': 'discount_rate',
                    'scope': '쇼핑',
                    'label': '쇼핑 10%',
                    'ratePercent': 10,
                    'excludedPaymentMethods': ['interest_free_installment'],
                }
            ],
        }

        lump_sum = _estimate_category_benefit(
            card,
            '쇼핑',
            100000,
            payment_context={'paymentType': 'lump_sum'},
        )
        interest_free = _estimate_category_benefit(
            card,
            '쇼핑',
            100000,
            payment_context={
                'paymentType': 'installment',
                'installmentMonths': 6,
                'isInterestFreeInstallment': True,
            },
        )

        self.assertEqual(lump_sum['estimatedBenefit'], 10000)
        self.assertEqual(interest_free['estimatedBenefit'], 0)
        self.assertIn('혜택 제외', interest_free['benefitLabel'])

    def test_installment_exclusion_blocks_all_installment_benefit(self):
        card = {
            'benefitItems': [
                {
                    'type': 'discount_rate',
                    'scope': '쇼핑',
                    'label': '쇼핑 10%',
                    'ratePercent': 10,
                    'excludedPaymentMethods': ['installment'],
                }
            ],
        }

        estimate = _estimate_category_benefit(
            card,
            '쇼핑',
            100000,
            payment_context={
                'paymentType': 'installment',
                'installmentMonths': 3,
                'isInterestFreeInstallment': False,
            },
        )

        self.assertEqual(estimate['estimatedBenefit'], 0)
        self.assertEqual(estimate['paymentLabel'], '3개월 할부')

    def test_monthly_limit_is_shared_across_split_rows(self):
        card = {
            'annualFee': 0,
            'benefitItems': [
                {
                    'type': 'discount_rate',
                    'scope': '쇼핑',
                    'label': '쇼핑 10%',
                    'ratePercent': 10,
                    'monthlyBenefitLimitKrw': 5000,
                }
            ],
        }
        profile = {
            'totalExpense': 100000,
            'benefitEvaluationRows': [
                {'category': '쇼핑', 'amount': 50000, 'paymentType': 'lump_sum'},
                {
                    'category': '쇼핑',
                    'amount': 50000,
                    'paymentType': 'installment',
                    'installmentMonths': 3,
                    'isInterestFreeInstallment': False,
                },
            ],
        }

        value = _estimate_card_value(card, profile)

        self.assertEqual(value['expectedMonthlyBenefit'], 5000)
        self.assertEqual(sum(row['estimatedBenefit'] for row in value['categoryBreakdown']), 5000)

    def test_previous_month_spend_controls_current_benefit(self):
        card = {
            'annualFee': 0,
            'previousMonthMinSpend': 300000,
            'benefitItems': [
                {
                    'type': 'discount_rate',
                    'scope': '쇼핑',
                    'label': '쇼핑 10%',
                    'ratePercent': 10,
                }
            ],
        }
        profile = {
            'totalExpense': 100000,
            'categoryRows': [{'category': '쇼핑', 'amount': 100000}],
        }

        value = _estimate_card_value(
            card,
            profile,
            benefit_eligibility_spend=0,
            performance_spend=350000,
        )

        self.assertFalse(value['eligibleForBenefit'])
        self.assertTrue(value['nextMonthEligibleForBenefit'])
        self.assertEqual(value['expectedMonthlyBenefit'], 0)
        self.assertEqual(value['potentialMonthlyBenefit'], 10000)
        self.assertEqual(value['remainingCurrentSpendForNextMonthBenefit'], 0)

    def test_routing_suggestions_only_use_owned_cards(self):
        owned_source = {
            'id': 'owned-source',
            'name': '보유 낮은 카드',
            'benefitItems': [{'type': 'discount_rate', 'scope': '쇼핑', 'label': '쇼핑 1%', 'ratePercent': 1}],
        }
        owned_target = {
            'id': 'owned-target',
            'name': '보유 높은 카드',
            'benefitItems': [{'type': 'discount_rate', 'scope': '쇼핑', 'label': '쇼핑 10%', 'ratePercent': 10}],
        }
        candidate = {
            'id': 'candidate-card',
            'cardAdId': 'candidate-card',
            'name': '새 후보 카드',
            'benefitItems': [{'type': 'discount_rate', 'scope': '쇼핑', 'label': '쇼핑 50%', 'ratePercent': 50}],
            'economics': {'monthlyDelta': 50000},
        }
        profile = {
            'categoryCardRows': [
                {'category': '쇼핑', 'cardId': 'owned-source', 'amount': 100000, 'paymentType': 'lump_sum'}
            ],
            'previousByCard': [
                {'cardId': 'owned-source', 'amount': 500000},
                {'cardId': 'owned-target', 'amount': 500000},
            ],
            'spendingTrend': {'categoryChanges': []},
        }

        suggestions = _build_routing_suggestions(
            profile,
            [{'card': owned_source}, {'card': owned_target}],
            [candidate],
            {'owned-source', 'owned-target'},
        )

        self.assertTrue(suggestions)
        self.assertTrue(all(item['toCardId'] in {'owned-source', 'owned-target'} for item in suggestions))
        self.assertFalse(any(item['toCardId'] == 'candidate-card' for item in suggestions))

    def test_plan_items_keep_payment_terms(self):
        items = normalize_plan_items(
            [
                {
                    'name': '노트북',
                    'category': '전자기기',
                    'amount': 1200000,
                    'targetMonth': '2026-07',
                    'paymentType': 'installment',
                    'installmentMonths': 12,
                    'isInterestFreeInstallment': True,
                }
            ]
        )

        self.assertEqual(items[0]['paymentType'], 'installment')
        self.assertEqual(items[0]['installmentMonths'], 12)
        self.assertTrue(items[0]['isInterestFreeInstallment'])

    def test_under_minimum_spend_has_zero_current_benefit(self):
        card = {
            'annualFee': 12000,
            'previousMonthMinSpend': 300000,
            'benefitItems': [
                {
                    'type': 'discount_rate',
                    'scope': '스타벅스 등 커피전문점',
                    'label': '스타벅스 등 커피전문점 7%',
                    'ratePercent': 7,
                }
            ],
        }
        profile = {
            'totalExpense': 10000,
            'categoryRows': [{'category': '카페', 'amount': 10000}],
        }

        value = _estimate_card_value(card, profile)

        self.assertFalse(value['eligibleForBenefit'])
        self.assertEqual(value['remainingSpendForBenefit'], 290000)
        self.assertEqual(value['expectedMonthlyBenefit'], 0)
        self.assertEqual(value['potentialMonthlyBenefit'], 700)

    def test_reason_uses_recurring_matched_category_before_one_time(self):
        card = {
            'annualFee': 0,
            'benefitItems': [
                {
                    'type': 'discount_rate',
                    'scope': '무신사 등 온라인몰',
                    'label': '무신사 등 온라인몰 7%',
                    'ratePercent': 7,
                },
                {
                    'type': 'discount_rate',
                    'scope': '맥도날드 등 외식브랜드',
                    'label': '맥도날드 등 외식브랜드 7%',
                    'ratePercent': 7,
                },
            ],
        }
        profile = {
            'totalExpense': 150000,
            'topCategory': '쇼핑',
            'recommendationTopCategory': '식비',
            'oneTimeCategories': ['쇼핑'],
            'categoryRows': [
                {'category': '쇼핑', 'amount': 100000},
                {'category': '식비', 'amount': 50000},
            ],
        }

        value = _estimate_card_value(card, profile)
        reason = _recommendation_reason(card, value, profile, 10000)

        self.assertEqual(value['primaryMatchedCategory'], '식비')
        self.assertIn('식비 소비 기준', reason)


class AuthApiTests(TestCase):
    def signup_user(self, email, name='사용자'):
        response = self.client.post(
            '/api/auth/email/signup/',
            data=json.dumps(
                {
                    'email': email,
                    'password': 'Carchpass123!',
                    'name': name,
                }
            ),
            content_type='application/json',
        )
        self.assertIn(response.status_code, {200, 201})
        return response.json()['token']

    def test_email_signup_me_and_logout_flow(self):
        signup = self.client.post(
            '/api/auth/email/signup/',
            data=json.dumps(
                {
                    'email': 'member@carch.test',
                    'password': 'Carchpass123!',
                    'name': '남주현',
                }
            ),
            content_type='application/json',
        )

        self.assertEqual(signup.status_code, 201)
        token = signup.json()['token']

        me = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(me.status_code, 200)
        self.assertTrue(me.json()['authenticated'])
        self.assertEqual(me.json()['user']['email'], 'member@carch.test')

        logout = self.client.post('/api/auth/logout/', HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(logout.status_code, 200)

        expired = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(expired.status_code, 401)

    def test_email_login_returns_token(self):
        self.client.post(
            '/api/auth/email/signup/',
            data=json.dumps(
                {
                    'email': 'login@carch.test',
                    'password': 'Carchpass123!',
                    'name': '로그인',
                }
            ),
            content_type='application/json',
        )

        login = self.client.post(
            '/api/auth/email/login/',
            data=json.dumps({'email': 'login@carch.test', 'password': 'Carchpass123!'}),
            content_type='application/json',
        )

        self.assertEqual(login.status_code, 200)
        self.assertIn('token', login.json())

    @override_settings(
        DEBUG=True,
        DEV_AUTO_LOGIN_ENABLED=True,
        DEV_ADMIN_EMAIL='admin@carch.test',
        DEV_ADMIN_PASSWORD='Carchadmin123!',
        DEV_ADMIN_NAME='테스트 관리자',
    )
    def test_dev_login_creates_admin_session(self):
        response = self.client.post('/api/auth/dev-login/')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['devAutoLogin'])
        self.assertEqual(payload['provider'], 'dev-admin')
        self.assertIn('token', payload)
        self.assertEqual(payload['user']['email'], 'admin@carch.test')

        User = get_user_model()
        user = User.objects.get(email='admin@carch.test')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password('Carchadmin123!'))

        me = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f"Bearer {payload['token']}")
        self.assertEqual(me.status_code, 200)
        self.assertTrue(me.json()['authenticated'])

    @override_settings(DEBUG=False, DEV_AUTO_LOGIN_ENABLED=True)
    def test_dev_login_is_blocked_when_debug_is_off(self):
        response = self.client.post('/api/auth/dev-login/')

        self.assertEqual(response.status_code, 403)

    @override_settings(KAKAO_CLIENT_ID='', KAKAO_CLIENT_SECRET='', NAVER_CLIENT_ID='', NAVER_CLIENT_SECRET='')
    def test_auth_providers_hide_unconfigured_oauth(self):
        response = self.client.get('/api/auth/providers/')

        self.assertEqual(response.status_code, 200)
        providers = {item['id']: item for item in response.json()['providers']}
        self.assertFalse(providers['kakao']['enabled'])
        self.assertFalse(providers['naver']['enabled'])

    def test_transactions_are_scoped_by_user(self):
        token_a = self.signup_user('a@carch.test', 'A')
        token_b = self.signup_user('b@carch.test', 'B')

        created = self.client.post(
            '/api/transactions/',
            data=json.dumps(
                {
                    'id': 'private-tx-a',
                    'cardId': '10029',
                    'merchantName': 'A 전용 결제',
                    'category': '식비',
                    'amount': -12000,
                    'approvedAt': '2026-06-23T12:00:00+09:00',
                }
            ),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token_a}',
        )
        self.assertEqual(created.status_code, 201)

        a_rows = self.client.get('/api/transactions/', HTTP_AUTHORIZATION=f'Bearer {token_a}').json()['results']
        b_rows = self.client.get('/api/transactions/', HTTP_AUTHORIZATION=f'Bearer {token_b}').json()['results']

        self.assertTrue(any(row['id'] == 'private-tx-a' for row in a_rows))
        self.assertFalse(any(row['id'] == 'private-tx-a' for row in b_rows))

    def test_transaction_create_persists_installment_terms(self):
        token = self.signup_user('installment@carch.test', 'Installment')

        response = self.client.post(
            '/api/transactions/',
            data=json.dumps(
                {
                    'id': 'installment-tx',
                    'cardId': '10612',
                    'merchantName': '쿠팡',
                    'category': '쇼핑',
                    'amount': -240000,
                    'approvedAt': '2026-06-23T12:00:00+09:00',
                    'paymentType': 'installment',
                    'installmentMonths': 6,
                    'isInterestFreeInstallment': True,
                }
            ),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload['paymentType'], 'installment')
        self.assertEqual(payload['installmentMonths'], 6)
        self.assertTrue(payload['isInterestFreeInstallment'])

    def test_transactions_require_valid_auth_token(self):
        anonymous = self.client.get('/api/transactions/')
        invalid = self.client.get('/api/transactions/', HTTP_AUTHORIZATION='Bearer invalid-token')

        self.assertEqual(anonymous.status_code, 401)
        self.assertEqual(invalid.status_code, 401)

    def test_seed_transactions_are_added_even_after_user_created_transaction(self):
        token = self.signup_user('seed-after-create@carch.test', 'Seed')

        self.client.post(
            '/api/transactions/',
            data=json.dumps(
                {
                    'id': 'first-user-tx',
                    'cardId': '10029',
                    'merchantName': '첫 결제',
                    'category': '식비',
                    'amount': -12000,
                    'approvedAt': '2026-06-23T12:00:00+09:00',
                }
            ),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        rows = self.client.get('/api/transactions/', HTTP_AUTHORIZATION=f'Bearer {token}').json()['results']
        summary = self.client.get('/api/analytics/spending-summary/', HTTP_AUTHORIZATION=f'Bearer {token}').json()

        self.assertGreater(len(rows), 1)
        self.assertGreater(summary['totalExpense'], 12000)

    def test_owned_cards_are_scoped_by_user(self):
        token_a = self.signup_user('card-a@carch.test', 'A')
        token_b = self.signup_user('card-b@carch.test', 'B')

        self.client.delete('/api/owned-cards/10029/', HTTP_AUTHORIZATION=f'Bearer {token_a}')

        a_cards = self.client.get('/api/owned-cards/', HTTP_AUTHORIZATION=f'Bearer {token_a}').json()['results']
        b_cards = self.client.get('/api/owned-cards/', HTTP_AUTHORIZATION=f'Bearer {token_b}').json()['results']

        self.assertFalse(any(str(card['cardAdId']) == '10029' for card in a_cards))
        self.assertTrue(any(str(card['cardAdId']) == '10029' for card in b_cards))

    def test_card_search_includes_full_catalog_beyond_owned_cards(self):
        token = self.signup_user('search-cards@carch.test', 'Search')

        response = self.client.get(
            '/api/search/?type=card&limit=50',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        self.assertEqual(response.status_code, 200)
        rows = response.json()['results']
        self.assertGreater(len(rows), 3)
        self.assertTrue(any(row['type'] == 'card' and row.get('badge') == '보유중' for row in rows))
        self.assertTrue(any(row['type'] == 'card' and row['path'].startswith('/cards/apply/') and not row.get('badge') for row in rows))
        self.assertFalse(any(row['type'] == 'card' and row.get('badge') == '비교 카드' for row in rows))

    def test_community_post_creation_requires_auth(self):
        response = self.client.post(
            '/api/community/posts/',
            data=json.dumps({'title': '익명 작성', 'body': '토큰 없는 작성'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)

    def test_community_post_edit_and_delete_require_owner(self):
        owner_token = self.signup_user('community-owner@carch.test', 'Owner')
        other_token = self.signup_user('community-other@carch.test', 'Other')

        created = self.client.post(
            '/api/community/posts/',
            data=json.dumps({'title': 'Owner post', 'body': 'Owner body'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {owner_token}',
        )
        self.assertEqual(created.status_code, 201)
        post_id = created.json()['id']

        forbidden_patch = self.client.patch(
            f'/api/community/posts/{post_id}/',
            data=json.dumps({'title': 'Other edit'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {other_token}',
        )
        self.assertEqual(forbidden_patch.status_code, 403)

        owner_patch = self.client.patch(
            f'/api/community/posts/{post_id}/',
            data=json.dumps({'title': 'Owner edit'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {owner_token}',
        )
        self.assertEqual(owner_patch.status_code, 200)
        self.assertEqual(owner_patch.json()['title'], 'Owner edit')

        forbidden_delete = self.client.delete(
            f'/api/community/posts/{post_id}/',
            HTTP_AUTHORIZATION=f'Bearer {other_token}',
        )
        self.assertEqual(forbidden_delete.status_code, 403)

        owner_delete = self.client.delete(
            f'/api/community/posts/{post_id}/',
            HTTP_AUTHORIZATION=f'Bearer {owner_token}',
        )
        self.assertEqual(owner_delete.status_code, 200)

    def test_community_post_likes_are_scoped_per_user(self):
        token_a = self.signup_user('like-a@carch.test', 'Like A')
        token_b = self.signup_user('like-b@carch.test', 'Like B')

        created = self.client.post(
            '/api/community/posts/',
            data=json.dumps({'title': 'Like target', 'body': 'Per-user like state'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token_a}',
        )
        self.assertEqual(created.status_code, 201)
        post_id = created.json()['id']

        liked_by_a = self.client.post(
            f'/api/community/posts/{post_id}/like/',
            HTTP_AUTHORIZATION=f'Bearer {token_a}',
        )
        self.assertEqual(liked_by_a.status_code, 200)
        self.assertTrue(liked_by_a.json()['liked'])
        self.assertEqual(liked_by_a.json()['likes'], 1)

        viewed_by_b = self.client.get(
            f'/api/community/posts/{post_id}/',
            HTTP_AUTHORIZATION=f'Bearer {token_b}',
        )
        self.assertEqual(viewed_by_b.status_code, 200)
        self.assertFalse(viewed_by_b.json()['liked'])
        self.assertEqual(viewed_by_b.json()['likes'], 1)

        liked_by_b = self.client.post(
            f'/api/community/posts/{post_id}/like/',
            HTTP_AUTHORIZATION=f'Bearer {token_b}',
        )
        self.assertEqual(liked_by_b.status_code, 200)
        self.assertTrue(liked_by_b.json()['liked'])
        self.assertEqual(liked_by_b.json()['likes'], 2)

        unliked_by_a = self.client.post(
            f'/api/community/posts/{post_id}/like/',
            HTTP_AUTHORIZATION=f'Bearer {token_a}',
        )
        self.assertEqual(unliked_by_a.status_code, 200)
        self.assertFalse(unliked_by_a.json()['liked'])
        self.assertEqual(unliked_by_a.json()['likes'], 1)

        viewed_again_by_b = self.client.get(
            f'/api/community/posts/{post_id}/',
            HTTP_AUTHORIZATION=f'Bearer {token_b}',
        )
        self.assertTrue(viewed_again_by_b.json()['liked'])
        self.assertEqual(viewed_again_by_b.json()['likes'], 1)
