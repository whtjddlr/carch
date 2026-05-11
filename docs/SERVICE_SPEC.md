# CARCH 구현 가능 서비스 명세서

## 1. 서비스 개요

CARCH는 사용자가 이미 보유한 신용카드 중에서 결제 예정 정보와 카드 혜택 조건을 비교하여 최적의 카드를 추천하는 서비스이다.

본 서비스는 신규 카드 발급 추천이 아니라, 사용자가 이미 가지고 있는 카드를 더 효율적으로 사용하도록 돕는 **보유 카드 운영 최적화 서비스**를 목표로 한다.

사용자는 카드명을 검색해 보유 카드를 등록하고, 결제 예정 가맹점, 카테고리, 금액을 입력하면 예상 혜택 금액, 전월 실적 충족 여부, 남은 혜택 한도, 예산 초과 여부를 함께 확인할 수 있다.

핵심 포지셔닝은 다음과 같다.

> CARCH는 카드 비교 서비스가 아니라, 사용자가 이미 보유한 카드를 더 잘 쓰게 해주는 보유 카드 운영 최적화 서비스이다.

## 2. 문제 정의

신용카드는 체크카드보다 혜택이 크지만, 사용자는 다음과 같은 이유로 혜택을 제대로 활용하지 못한다.

- 카드별 전월 실적 조건이 복잡하다.
- 카테고리별 할인율과 월 할인한도를 기억하기 어렵다.
- 어떤 카드가 현재 결제에 가장 유리한지 직접 계산하기 번거롭다.
- 신용카드 과소비가 걱정되어 혜택이 적은 체크카드를 사용하는 경우가 있다.
- 보유 카드가 여러 장이면 혜택 중복과 활용도 낮은 카드를 파악하기 어렵다.

CARCH는 이 문제를 사용자의 보유 카드 데이터와 결제 예정 정보를 기반으로 해결한다.

## 3. MVP 범위

### 3.1 MVP 포함 기능

- 회원가입 및 로그인
- 카드명 유사 검색
- 보유 카드 등록
- 카드별 실적 및 혜택 한도 조회
- 소비 내역 직접 입력
- 결제 예정 정보 입력
- 보유 카드 중 최적 카드 추천
- 추천 사유 표시
- 월 예산 및 카테고리별 예산 관리
- 간단한 월간 소비/혜택 리포트

### 3.2 MVP 제외 기능

- 신규 카드 발급 추천
- OS 수준의 실시간 결제 감지
- 카드사 API 및 마이데이터 API 연동
- 자동 결제 차단
- 자동 저축/투자
- 실제 금융 거래 실행
- 모든 카드 혜택 조건의 100% 자동 계산

MVP에서는 사용자가 결제 예정 정보를 직접 입력했을 때 사전 추천을 제공한다. 실시간 결제 감지는 확장 기능으로 분리한다.

## 4. 핵심 사용자 흐름

1. 사용자는 회원가입 후 로그인한다.
2. 사용자는 본인이 보유한 카드를 검색해 등록한다.
3. 카드명은 정확히 입력하지 않아도 유사 후보를 제공한다.
4. 사용자는 현재 월 카드 사용액, 전월 사용액, 현재 혜택 사용액을 입력하거나 fixture 데이터를 불러온다.
5. 사용자는 결제 예정 가맹점, 카테고리, 결제 금액을 입력한다.
6. 시스템은 사용자의 보유 카드 중 혜택 적용 가능한 카드를 찾는다.
7. 전월 실적, 최소 결제 금액, 남은 월 혜택 한도, 예산 상태를 반영해 예상 혜택을 계산한다.
8. 가장 적합한 카드를 추천하고 추천 사유를 함께 제공한다.
9. 추천 결과는 이후 리포트와 카드 효율 분석에 활용된다.

## 5. 데이터 구축 현황

카드 데이터는 네이버 카드 정보를 기반으로 구축한 정형 데이터를 사용한다.

현재 구축된 데이터는 다음과 같다.

- 카드 상품 데이터: 381개
- 실사용 혜택 규칙: 2,811개
- 자동 계산 가능 규칙: 1,334개
- RAG용 혜택 문서: 2,811개
- 신규 가입/연회비 지원 혜택: 추천 DB에서 제외
- 카드명 유사 검색 인덱스: 381개 카드 기준 생성

추천 엔진은 AI 응답이 아니라 정형화된 혜택 규칙 데이터를 기반으로 계산한다.

복합 패키지형 혜택이나 다중 할인율이 포함된 규칙은 `needs_review` 플래그로 분리한다. MVP에서는 `calculation_ready = true`인 규칙을 우선 사용한다.

## 6. 주요 데이터 파일

프로젝트 내 카드 데이터 파일은 다음 위치에 저장되어 있다.

- `card_benefit_db/output/card_products.json`
- `card_benefit_db/output/card_benefit_rules.json`
- `card_benefit_db/output/recommendation_rules.json`
- `card_benefit_db/output/recommendation_rules_by_issuer.json`
- `card_benefit_db/output/recommendation_rules_by_category.json`
- `card_benefit_db/output/card_products_by_issuer.json`
- `card_benefit_db/output/card_name_search_index.json`
- `card_benefit_db/output/card_benefits.sqlite`

## 7. 데이터 구조

### 7.1 CardProduct

카드 상품 기본 정보를 저장한다.

| 필드명 | 설명 |
|---|---|
| id | 내부 카드 상품 ID |
| card_ad_id | 네이버 카드 기준 카드 ID |
| card_name | 카드명 |
| issuer_name | 카드사명 |
| issuer_code | 카드사 코드 |
| domestic_annual_fee | 국내 연회비 |
| foreign_annual_fee | 해외겸용 연회비 |
| previous_month_min_spend | 기본 전월 실적 기준 |
| naver_url | 네이버 카드 상세 URL |
| official_url | 카드사 공식 상세 URL |

### 7.2 RecommendationRule

추천 엔진에서 사용하는 계산용 혜택 규칙이다.

| 필드명 | 설명 |
|---|---|
| rule_id | 혜택 규칙 ID |
| card_ad_id | 카드 상품 ID |
| card_name | 카드명 |
| issuer_name | 카드사명 |
| category_name | 원본 카테고리명 |
| normalized_category | 추천 엔진용 표준 카테고리 |
| benefit_type | 혜택 타입 |
| primary_rate_percent | 대표 할인/적립률 |
| fixed_discount_amount_krw | 정액 할인 금액 |
| required_previous_month_spend_krw | 전월 실적 조건 |
| monthly_benefit_limit_krw | 월 혜택 한도 |
| yearly_benefit_limit_krw | 연 혜택 한도 |
| min_payment_amount_krw | 최소 결제 금액 |
| target_merchants | 적용 가맹점 후보 |
| exclusion_keywords | 제외 조건 키워드 |
| condition_lines | 조건 원문 |
| calculation_ready | 자동 계산 가능 여부 |
| needs_review | 검수 필요 여부 |
| review_flags | 검수 필요 사유 |

### 7.3 User

서비스 사용자를 저장한다.

| 필드명 | 설명 |
|---|---|
| id | 사용자 ID |
| email | 이메일 |
| password | 비밀번호 해시 |
| nickname | 닉네임 |
| created_at | 가입일 |

### 7.4 UserCardHolding

사용자가 보유한 카드를 저장한다.

| 필드명 | 설명 |
|---|---|
| id | 보유 카드 ID |
| user_id | 사용자 ID |
| card_product_id | 카드 상품 ID |
| current_month_spend | 현재 월 사용액 |
| previous_month_spend | 전월 사용액 |
| current_month_benefit_used | 현재 월 혜택 사용액 |
| is_active | 사용 여부 |

### 7.5 PaymentTransaction

사용자의 소비 내역을 저장한다.

| 필드명 | 설명 |
|---|---|
| id | 소비 내역 ID |
| user_id | 사용자 ID |
| card_holding_id | 사용 카드 ID |
| merchant_name | 가맹점명 |
| category | 소비 카테고리 |
| amount | 결제 금액 |
| paid_at | 결제일 |
| benefit_amount | 적용 혜택 금액 |

### 7.6 Budget

월 예산과 카테고리별 예산을 저장한다.

| 필드명 | 설명 |
|---|---|
| id | 예산 ID |
| user_id | 사용자 ID |
| category | 예산 카테고리 |
| monthly_limit | 월 예산 |
| current_spend | 현재 사용액 |

### 7.7 RecommendationResult

결제 추천 결과를 저장한다.

| 필드명 | 설명 |
|---|---|
| id | 추천 결과 ID |
| user_id | 사용자 ID |
| merchant_name | 가맹점명 |
| category | 소비 카테고리 |
| amount | 결제 예정 금액 |
| recommended_card_id | 추천 카드 ID |
| expected_benefit_amount | 예상 혜택 금액 |
| reason | 추천 사유 |
| created_at | 추천 생성일 |

## 8. 표준 카테고리

카드 혜택 카테고리는 추천 엔진에서 다음과 같이 표준화한다.

| 원본 카테고리 | 표준 카테고리 |
|---|---|
| 대중교통 | transport |
| 카페/베이커리 | cafe_bakery |
| 편의점 | convenience_store |
| 쇼핑 | shopping |
| 통신 | telecom |
| 영화 | movie |
| 외식 | dining |
| 주유 | fuel |
| 대형마트 | mart |
| 의료 | medical |
| 교육 | education |
| 간편결제 | easy_payment |
| 포인트/캐시백 | point_cashback |
| 프리미엄 | premium |
| 항공마일리지 | air_mileage |
| 관리비 | maintenance_fee |
| 공과금 | utility_bill |

## 9. 추천 엔진 명세

추천 엔진은 다음 순서로 동작한다.

1. 사용자가 입력한 카테고리와 가맹점명을 기준으로 혜택 규칙 후보를 조회한다.
2. 사용자가 등록한 보유 카드에 해당하는 규칙만 필터링한다.
3. `calculation_ready = true`인 규칙을 우선 사용한다.
4. 전월 실적 조건을 충족하지 못한 카드는 혜택 적용 불가 또는 낮은 우선순위로 처리한다.
5. 최소 결제 금액 조건이 있는 경우 결제 금액과 비교한다.
6. 월 혜택 한도가 있는 경우 이미 사용한 혜택 금액을 차감한다.
7. 할인율 또는 정액 할인 금액을 기준으로 예상 혜택 금액을 계산한다.
8. 예상 혜택 금액이 가장 큰 카드를 추천한다.
9. 예상 혜택 금액이 동일한 경우 남은 혜택 한도와 예산 초과 여부를 기준으로 정렬한다.
10. 예산 초과가 예상되는 경우 추천 결과에 경고를 함께 표시한다.

### 9.1 예상 혜택 계산 방식

할인율 기반 혜택:

```text
예상 혜택 금액 = 결제 금액 x 할인율
```

정액 할인 기반 혜택:

```text
예상 혜택 금액 = 정액 할인 금액
```

월 한도가 있는 경우:

```text
최종 예상 혜택 금액 = min(예상 혜택 금액, 월 혜택 한도 - 현재 월 혜택 사용액)
```

최소 결제 금액이 있는 경우:

```text
결제 금액 < 최소 결제 금액이면 혜택 적용 불가
```

전월 실적 조건이 있는 경우:

```text
전월 사용액 < 전월 실적 조건이면 혜택 적용 불가
```

## 10. 추천 결과 표시 정보

추천 결과 화면에는 다음 정보를 제공한다.

- 추천 카드명
- 예상 혜택 금액
- 혜택 적용 카테고리
- 전월 실적 충족 여부
- 남은 월 혜택 한도
- 최소 결제 금액 충족 여부
- 예산 초과 여부
- 다른 보유 카드와의 예상 혜택 비교
- 추천 사유

예시:

```text
삼성카드 taptap O를 추천합니다.

예상 혜택: 1,200원
추천 사유:
- 카페/베이커리 카테고리 혜택 대상입니다.
- 전월 실적 300,000원을 충족했습니다.
- 남은 월 혜택 한도 안에서 적용 가능합니다.
- 다른 보유 카드보다 예상 혜택이 큽니다.
```

## 11. 카드명 유사 검색 명세

사용자가 카드명을 정확히 입력하지 않아도 유사 카드 후보를 제공한다.

검색 방식은 다음 요소를 함께 사용한다.

- 카드명 정규화
- 공백 및 특수문자 제거
- 카드사명 별칭
- 수동 별칭
- 문자열 유사도 점수

예시:

| 사용자 입력 | 추천 후보 |
|---|---|
| 탭탭오 | 삼성카드 taptap O |
| taptap o | 삼성카드 taptap O |
| 굿데이 | KB국민 굿데이카드 |
| 국민 굿데이 올림 | KB국민 굿데이올림카드 |
| 위시 트래블 | KB국민 WE:SH Travel 카드 |
| 마이위시 | KB국민 My WE:SH 카드 |
| 미스터라이프 | 신한카드 Mr.Life |
| 딥오일 | 신한카드 Deep Oil |
| 아이디 심플 | 삼성 iD SIMPLE 카드 |
| 로카 라이킷 | LOCA LIKIT 1.2 |

MVP에서는 자동 확정보다 후보 3~5개를 보여주고 사용자가 선택하는 방식을 사용한다.

## 12. 주요 화면

### 12.1 홈 대시보드

- 이번 달 예산 사용률
- 이번 달 누적 혜택
- 보유 카드 실적 현황
- 결제 추천 바로가기

### 12.2 보유 카드 관리

- 카드명 검색
- 유사 카드 후보 표시
- 보유 카드 등록/삭제
- 카드별 현재 사용액 입력
- 카드별 전월 사용액 입력

### 12.3 카드 실적/한도 현황

- 카드별 전월 실적 조건
- 현재 월 사용액
- 남은 실적 금액
- 남은 혜택 한도
- 실적 달성률 표시

### 12.4 결제 추천

- 가맹점명 입력
- 카테고리 선택
- 결제 금액 입력
- 추천 실행

### 12.5 추천 결과

- 추천 카드
- 예상 혜택 금액
- 추천 사유
- 다른 보유 카드 비교
- 예산 초과 경고

### 12.6 소비 내역

- 결제 내역 직접 입력
- 카테고리 필터
- 카드별 사용 내역 조회
- CSV 업로드 확장 영역

### 12.7 예산 관리

- 월 전체 예산 설정
- 카테고리별 예산 설정
- 현재 사용률 표시
- 초과 경고

### 12.8 카드 효율 분석

- 카드별 혜택 이용률
- 혜택 중복 카테고리
- 활용도 낮은 카드 표시
- 향후 카드 사용 전략 제안

### 12.9 월간 리포트

- 카테고리별 소비 금액
- 카드별 혜택 금액
- 예산 준수율
- 월별 소비 추이

## 13. API 명세

### 13.1 인증

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/api/auth/signup/` | 회원가입 |
| POST | `/api/auth/login/` | 로그인 |
| POST | `/api/auth/logout/` | 로그아웃 |
| GET | `/api/auth/me/` | 내 정보 조회 |

### 13.2 카드 상품

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/cards/search/?q=` | 카드명 유사 검색 |
| GET | `/api/cards/products/` | 카드 상품 목록 |
| GET | `/api/cards/products/{id}/` | 카드 상품 상세 |
| GET | `/api/cards/categories/` | 혜택 카테고리 목록 |

### 13.3 보유 카드

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/api/user-cards/` | 보유 카드 등록 |
| GET | `/api/user-cards/` | 보유 카드 목록 |
| GET | `/api/user-cards/{id}/` | 보유 카드 상세 |
| PATCH | `/api/user-cards/{id}/` | 보유 카드 사용액 수정 |
| DELETE | `/api/user-cards/{id}/` | 보유 카드 삭제 |

### 13.4 소비 내역

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/api/transactions/` | 소비 내역 등록 |
| GET | `/api/transactions/` | 소비 내역 조회 |
| GET | `/api/transactions/{id}/` | 소비 내역 상세 |
| PATCH | `/api/transactions/{id}/` | 소비 내역 수정 |
| DELETE | `/api/transactions/{id}/` | 소비 내역 삭제 |

### 13.5 추천

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/api/recommendations/simulate/` | 결제 추천 실행 |
| GET | `/api/recommendations/history/` | 추천 기록 조회 |
| GET | `/api/recommendations/{id}/` | 추천 결과 상세 |

### 13.6 예산

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/budgets/` | 예산 조회 |
| POST | `/api/budgets/` | 예산 설정 |
| PATCH | `/api/budgets/{id}/` | 예산 수정 |
| DELETE | `/api/budgets/{id}/` | 예산 삭제 |

### 13.7 리포트

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/reports/monthly/` | 월간 리포트 |
| GET | `/api/reports/card-efficiency/` | 보유 카드 효율 분석 |

## 14. 결제 추천 API 요청/응답 예시

### 14.1 요청

```json
{
  "merchant_name": "스타벅스",
  "category": "cafe_bakery",
  "amount": 12000
}
```

### 14.2 응답

```json
{
  "recommended_card": {
    "card_holding_id": 1,
    "card_name": "삼성카드 taptap O",
    "issuer_name": "삼성카드"
  },
  "expected_benefit_amount": 1200,
  "budget_warning": false,
  "reasons": [
    "카페/베이커리 혜택 대상입니다.",
    "전월 실적 조건을 충족했습니다.",
    "남은 월 혜택 한도 안에서 적용 가능합니다."
  ],
  "comparisons": [
    {
      "card_name": "삼성카드 taptap O",
      "expected_benefit_amount": 1200,
      "applicable": true
    },
    {
      "card_name": "신한카드 Mr.Life",
      "expected_benefit_amount": 600,
      "applicable": true
    },
    {
      "card_name": "KB국민 굿데이카드",
      "expected_benefit_amount": 0,
      "applicable": false,
      "reason": "해당 카테고리 혜택 규칙이 없습니다."
    }
  ]
}
```

## 15. 테스트 시나리오

### 15.1 테스트 사용자

사용자 A의 보유 카드:

- 삼성카드 taptap O
- 신한카드 Mr.Life
- KB국민 굿데이카드

### 15.2 테스트 결제

| 결제 상황 | 기대 결과 |
|---|---|
| 스타벅스 12,000원 | 카페 혜택이 가장 큰 카드 추천 |
| 버스 1,500원 | 대중교통 혜택이 있는 카드 추천 |
| 쿠팡 48,000원 | 쇼핑/온라인몰 혜택이 있는 카드 추천 |
| 통신비 70,000원 | 통신 자동납부 혜택 카드 추천 |
| CGV 15,000원 | 영화 정액 할인 카드 추천 |

## 16. 검증 기준

MVP 완료 기준은 다음과 같다.

- 사용자가 카드명을 일부만 입력해도 카드 후보가 조회된다.
- 사용자가 보유 카드를 등록할 수 있다.
- 결제 예정 정보를 입력하면 보유 카드 중 하나가 추천된다.
- 추천 결과에 예상 혜택 금액과 추천 사유가 표시된다.
- 전월 실적 조건이 추천 계산에 반영된다.
- 월 혜택 한도가 추천 계산에 반영된다.
- 최소 결제 금액 조건이 추천 계산에 반영된다.
- 신규 카드나 보유하지 않은 카드는 추천 후보에 포함되지 않는다.
- 신규 가입/연회비 지원 혜택은 추천 계산에 포함되지 않는다.
- 동일 fixture 데이터로 동일 추천 결과가 재현된다.

## 17. 우선순위

### Must Have

- 회원가입/로그인
- 카드명 유사 검색
- 보유 카드 등록
- 카드 상품/혜택 데이터 import
- 결제 예정 정보 입력
- 보유 카드 기반 최적 카드 추천
- 추천 사유 표시

### Should Have

- 소비 내역 직접 입력
- 카드별 실적/한도 현황
- 예산 설정 및 초과 경고
- 월간 리포트

### Could Have

- CSV/엑셀 소비 내역 업로드
- 보유 카드 효율 분석
- RAG 기반 혜택 원문 검색
- 복합 혜택 검수 화면

### Won't Have

- 신규 카드 발급 추천
- 실시간 결제 감지
- 카드사 API 연동
- 마이데이터 연동
- 자동 저축/투자

## 18. 개발 순서

1. Django/DRF 프로젝트 생성
2. DB 모델 생성
3. 카드 상품/혜택 데이터 import
4. 카드명 유사 검색 API 구현
5. 보유 카드 등록 API 구현
6. 결제 추천 엔진 구현
7. 결제 추천 API 구현
8. 소비 내역/예산 API 구현
9. 프론트엔드 화면 구현
10. 테스트 fixture 작성
11. 발표용 시나리오 검증

## 19. 확장 기능

향후 확장 가능한 기능은 다음과 같다.

- CSV/엑셀 소비 내역 업로드
- RAG 기반 카드 혜택 원문 검색
- 복합 패키지형 혜택 검수 화면
- 카드사 공식 상품설명서 기반 데이터 보강
- 보유 카드 효율 분석 고도화
- 신규 카드 추천
- 마이데이터 연동
- 결제 알림 기반 반자동 추천

## 20. 리스크 및 대응

| 리스크 | 대응 |
|---|---|
| 카드 혜택 조건이 복잡해 자동 계산이 어려움 | calculation_ready와 needs_review를 분리해 안정적인 규칙부터 사용 |
| 실시간 결제 감지가 어려움 | MVP에서는 사용자가 결제 예정 정보를 직접 입력 |
| 카드 데이터 변경 가능성 | 출처 URL 저장 및 데이터 재수집 스크립트 유지 |
| 사용자 소비 데이터 자동 연동 어려움 | 직접 입력과 fixture 기반으로 시작하고 CSV 업로드로 확장 |
| 추천 결과 신뢰성 문제 | 추천 사유와 적용 조건을 함께 표시 |

