# 카드 데이터셋 요약

## 데이터 목적

CARCH의 추천 엔진은 AI 응답이 아니라 정형화된 카드 혜택 규칙을 기반으로 계산합니다. 이 문서는 프로젝트에서 사용할 카드 데이터셋의 범위와 활용 방식을 정리합니다.

## 구축 현황

| 항목 | 수량 |
|---|---:|
| 카드 상품 데이터 | 381개 |
| 실사용 혜택 규칙 | 2,811개 |
| 자동 계산 가능 규칙 | 1,334개 |
| RAG용 혜택 문서 | 2,811개 |
| 제외한 신규/연회비성 혜택 | 131개 |

## 주요 데이터 구조

### CardProduct

카드 상품 기본 정보입니다.

- 카드명
- 카드사
- 연회비
- 전월 실적 기준
- 네이버 카드 상세 URL
- 카드사 공식 URL

### RecommendationRule

추천 엔진에서 사용하는 계산용 혜택 규칙입니다.

- 표준 카테고리
- 혜택 타입
- 대표 할인/적립률
- 정액 할인 금액
- 전월 실적 조건
- 월 혜택 한도
- 최소 결제 금액
- 적용 가맹점 후보
- 제외 조건 키워드
- 자동 계산 가능 여부
- 검수 필요 여부

## 추천 엔진 적용 기준

MVP에서는 `calculation_ready = true`인 규칙을 우선 사용합니다.

복합 패키지형 혜택, 다중 할인율, 여러 카테고리 한도가 섞인 혜택은 `needs_review = true`로 분리합니다.

## 로컬 데이터 파일 위치

현재 작업 환경 기준 데이터 파일은 다음 경로에 생성되어 있습니다.

```text
C:/Users/SSAFY/Desktop/pjtjuhyun/card_benefit_db/output/card_products.json
C:/Users/SSAFY/Desktop/pjtjuhyun/card_benefit_db/output/recommendation_rules.json
C:/Users/SSAFY/Desktop/pjtjuhyun/card_benefit_db/output/recommendation_rules_by_issuer.json
C:/Users/SSAFY/Desktop/pjtjuhyun/card_benefit_db/output/recommendation_rules_by_category.json
C:/Users/SSAFY/Desktop/pjtjuhyun/card_benefit_db/output/card_name_search_index.json
C:/Users/SSAFY/Desktop/pjtjuhyun/card_benefit_db/output/card_benefits.sqlite
```

대용량 JSON/SQLite 파일은 초기 레포에는 포함하지 않고, 필요 시 데이터 import 단계에서 추가합니다.

