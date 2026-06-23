import json

from django.test import SimpleTestCase, TestCase, override_settings

from .views import (
    _benefit_rate_for_category,
    _estimate_card_value,
    _recommendation_reason,
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
