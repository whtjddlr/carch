# CARCH App Store Readiness

이 문서는 CARCH를 포트폴리오 웹앱이 아니라 App Store 제출 가능한 iOS 앱으로 전환하기 위한 작업 목록이다.

## 현재 기준

- iOS 패키징: Capacitor 프로젝트 생성 완료
- Bundle ID: `com.choim2013.carch`
- 서비스 웹: https://carch.vercel.app
- 서비스 API: https://carch-api.vercel.app
- 시연/demo 웹: https://carch-demo.vercel.app/demo
- 시연/demo API: 프론트 mock/데모 채널 기준. 별도 demo 백엔드를 붙일 때만 `BACKEND_URL_DEMO`를 설정한다.
- iOS API: service 빌드는 `VITE_IOS_API_BASE_URL=https://carch-api.vercel.app`로 동기화함
- service 백엔드: 별도 Vercel 프로젝트/도메인과 `DATABASE_SCHEMA=service` 환경 사용
- 네이티브 토큰 저장: iOS/Android에서는 Keychain/Keystore 기반 Secure Storage 사용
- 웹 토큰 저장: 브라우저에서는 기존처럼 `localStorage` 사용
- 백엔드 CORS 기본값: `capacitor://localhost`, `ionic://localhost` 허용 추가
- 배포 채널: 포트폴리오/시연은 `demo`, App Store/서비스는 `service`로 분리
- App Store 배포 범위: 대한민국
- App Store 지원 기기: iPhone 전용
- service/App Store 카드 아트워크: 실카드 이미지 파일은 번들에서 제외하고, 중립 카드 UI와 CARCH 자체 캐릭터 이미지(`magpie-face*.png`)만 포함한다.

## App Store Connect 현재 상태

- 앱 이름: `CARCH`
- 버전: `1.0`
- 연결 빌드: `7`
- 빌드 상태: `제출 준비 완료`
- 업로드된 최신 빌드: `7` (실카드 이미지 제거)
- 카테고리: `FINANCE`
- 개인정보 처리방침 URL: https://carch.vercel.app/privacy
- 지원 URL: https://carch.vercel.app/privacy
- iPhone 6.7/6.9 스크린샷: 6장 업로드 완료, App Store Connect asset state `COMPLETE`
- 저장소 보관 경로: `docs/screenshots/appstore/iphone-6-9/`
- 가격: 무료, 기준 국가/통화 `대한민국(KRW)`
- 사용 가능 국가/지역: `대한민국` 1개 사용 가능, 174개 사용 불가
- Apple Silicon Mac 배포: 비활성
- Apple Vision Pro 배포: 비활성
- App Privacy: 게시 완료
- 현재 App Store 상태: `PREPARE_FOR_SUBMISSION`
- 남은 수동 확인: 콘텐츠 권한. service/App Store 번들에서 실카드 이미지 파일은 제거했지만, 카드사명, 상품명, 혜택 데이터 등 타사 콘텐츠에 대한 필요한 권한이 있는지 확인 후 App Store Connect에서 저장해야 한다.

심사용 계정은 App Store Connect의 App Review Information에만 저장한다. 공개 저장소 README/문서에는 심사용 비밀번호를 커밋하지 않는다.

## App Review 리스크

- Apple Guideline 4.2는 단순 웹사이트 재포장 수준의 앱을 거절 위험으로 본다. CARCH는 Face ID 잠금, 네이티브 알림, 공유, 위젯 등 앱다운 기능을 추가해야 한다.
- 계정 생성이 있으므로 앱 안에서 계정 삭제를 시작할 수 있어야 한다. 현재는 `DELETE /api/auth/account/`와 설정 화면 계정 삭제 진입점이 있다.
- 개인정보 처리방침 URL이 필요하다. 현재 앱 내 `/privacy` 화면을 제공하며, App Store Connect 개인정보 라벨에는 계정 정보, 소비/거래 입력 데이터, 카드/추천 사용 데이터, AI 질의 데이터를 정확히 반영해야 한다.
- service/App Store 번들에는 실카드 이미지 파일을 포함하지 않는다. 카드사명, 상품명, 혜택 데이터 사용 권한과 출처는 제출 전 확인해야 한다.
- 추천 결과에는 실제 카드사 정책과 다를 수 있다는 고지가 필요하다.
- 카카오/네이버 로그인은 웹 배포에서는 유지하되, App Store용 iOS 앱에서는 숨긴다. iOS 제출 빌드는 자체 이메일 가입/로그인만 제공해서 Sign in with Apple 추가 요구 리스크를 줄인다.
- OAuth 코드는 iOS 콜백도 처리할 수 있게 유지한다. 이후 Apple 로그인까지 추가하기로 결정하면 같은 redirect 구조를 재사용할 수 있다.
- service 채널에서도 커뮤니티를 제공한다. App Review 리스크를 낮추려면 신고, 숨김, 작성자 삭제, 운영자 대응 정책을 심사 노트와 앱 설명에 일관되게 반영해야 한다.
- 배포 API `https://carch-api.vercel.app/api/auth/providers/` 기준으로 카카오/네이버 provider가 비활성(`enabled:false`)이면 Vercel 백엔드 환경변수에 `KAKAO_CLIENT_ID` 또는 `KAKAO_REST_API_KEY`, 필요 시 `KAKAO_CLIENT_SECRET`이 설정되어 있는지 확인해야 한다.

## 1차 필수 작업

- [x] Capacitor iOS 프로젝트 추가
- [x] iOS 빌드/동기화 스크립트 추가
- [x] 네이티브 보안 저장소 연결
- [x] iOS WebView Origin CORS 기본값 추가
- [x] 계정 삭제 API 추가
- [x] 설정 화면에 계정 삭제 진입점 추가
- [x] 개인정보 처리방침 페이지 추가
- [x] 추천/AI 결과에 금융 고지 문구 추가
- [x] 소셜 로그인 iOS 콜백 정책 결정
- [x] iOS 제출 빌드에서 제3자 소셜 로그인 제외 결정
- [x] service 채널에서 `/demo`, dev-login, 자동 seed 차단
- [x] service 채널에서 커뮤니티 작성/삭제/신고/숨김 흐름 유지
- [x] service iOS 번들에서 실카드 이미지 파일 제외
- [ ] service iOS 번들에서 demo 계정 문자열과 mock 데이터를 제외
- [x] service 백엔드 Vercel 프로젝트 생성 및 `BACKEND_URL_SERVICE`/`VITE_IOS_API_BASE_URL` 연결
- [x] App Store Review용 service 계정 생성
- [x] App Store Connect 메타데이터/스크린샷/build 6 연결
- [x] App Store Connect build 7 업로드
- [x] App Store Connect build 7 연결
- [x] App Store Connect App Privacy 설문 게시
- [x] App Store Connect 가격 무료 설정 및 대한민국만 사용 가능하도록 제한
- [x] iOS 앱 빌드 번호 7에 iPhone 전용 설정 및 수출 규정 키 반영
- [ ] App Store Connect 콘텐츠 권한 확인 및 저장

## Demo / Service 분리

시연용과 서비스용은 같은 코드베이스를 쓰되 배포 환경변수, DB, Vercel 프로젝트를 분리한다.

```txt
demo:
APP_CHANNEL=demo
DEMO_FEATURES_ENABLED=true
DATABASE_SCHEMA=demo
CARD_CATALOG_SCHEMA=catalog
DATABASE_SEARCH_PATH=demo,catalog
CARD_CATALOG_SOURCE=postgres
VITE_APP_CHANNEL=demo
같은 Supabase DB의 demo schema 사용

service:
APP_CHANNEL=service
DEMO_FEATURES_ENABLED=false
DEV_AUTO_LOGIN_ENABLED=false
DATABASE_SCHEMA=service
CARD_CATALOG_SCHEMA=catalog
DATABASE_SEARCH_PATH=service,catalog
CARD_CATALOG_SOURCE=postgres
VITE_APP_CHANNEL=service
같은 Supabase DB의 service schema 사용
```

하나의 Supabase 프로젝트 안에서 `demo`, `service`, `catalog` schema를 나눈다. Django 앱 테이블(`auth_user`, `transactions`, `django_migrations` 등)은 마이그레이션 시 `DATABASE_SEARCH_PATH` 첫 번째 schema(= `DATABASE_SCHEMA`)에 생성된다. 그래서 `DATABASE_SEARCH_PATH`는 반드시 `DATABASE_SCHEMA`로 시작해야 한다. (이전 문서의 `DATABASE_SEARCH_PATH=catalog`는 앱 테이블을 catalog에 잘못 생성하므로 사용하지 않는다.)

런타임 조회는 search_path에 의존하지 않는다. 앱 모델 테이블은 `"schema"."table"`로 한정되고(`api/db_schema.py`), 카드 카탈로그 SQL도 `"catalog".cards`처럼 스키마를 명시한다(`api/card_repository.py`). 따라서 Supabase 트랜잭션 풀러(6543)가 `SET search_path`를 트랜잭션마다 리셋해도 런타임 API는 영향받지 않는다.

단, **마이그레이션(`migrate`)은 세션이 유지되는 direct 연결(포트 5432 / session mode)로 실행한다.** 트랜잭션 풀러로 migrate하면 `SET search_path`가 유지되지 않아 앱 테이블이 엉뚱한 schema에 생성될 수 있다.

`public`에는 기존 테이블이 남아 있을 수 있으므로 demo/service 배포의 search_path에는 넣지 않는다. 서비스용 schema는 카드 카탈로그만 공용으로 참조하고, `auth_user`, `transactions`, `owned_cards`, `purchase_plans`, `community_posts`, `ai_analysis_records`는 비어 있어야 한다. service 채널에서는 마이그레이션, 런타임 API, `seed_demo` 명령이 데모 유저와 데모 데이터를 만들지 않는다.

Supabase SQL Editor에서 최초 1회 schema를 만든다.

```sql
create schema if not exists catalog;
create schema if not exists demo;
create schema if not exists service;
```

`demo`/`service` schema는 Data API에 노출하지 않는다. 백엔드가 Postgres 연결로만 접근한다. Supabase REST API로 custom schema를 노출하려면 별도 API 설정과 GRANT가 필요하지만, CARCH 서비스 데이터에는 적용하지 않는다.

## 2차 앱다운 기능

- [ ] Face ID/Touch ID 앱 잠금
- [ ] 로컬 알림: 예산 초과, 결제 입력 리마인더
- [ ] 네이티브 공유: 추천 카드/소비 리포트 공유
- [ ] App Icon, Launch Screen, Splash Asset 정리
- [ ] TestFlight 실제 기기 검증
- [ ] Sentry 또는 동급 에러 모니터링

## 빌드 명령

```bash
cd frontend
npm run ios:sync
npm run ios:open
```

`ios:sync`는 기본적으로 `VITE_APP_CHANNEL=service`로 빌드한다. service 빌드는 mock API를 사용하지 않으며, `VITE_IOS_API_BASE_URL`이 없으면 실패한다.

```bash
VITE_IOS_API_BASE_URL=https://<service-backend-vercel-domain> npm run ios:sync
```

현재 서비스 API 기준:

```bash
VITE_IOS_API_BASE_URL=https://carch-api.vercel.app npm run ios:sync
```

로컬에서 WebView 셸만 임시 검증할 때도 service API를 지정해 실제 로그인/계정 삭제 흐름을 확인한다.

## Vercel 환경변수 주의

백엔드 Vercel 프로젝트에서 `CORS_ALLOWED_ORIGINS`를 직접 설정했다면 아래 Origin을 추가해야 iOS 앱에서 API 호출이 막히지 않는다.

```txt
capacitor://localhost,ionic://localhost
```

OAuth를 iOS 앱 안으로 되돌리려면 `OAUTH_ALLOWED_FRONTEND_REDIRECTS`에도 같은 Origin이 들어가야 한다.

카카오 개발자 콘솔에는 백엔드 콜백 URL이 등록되어 있어야 한다.

```txt
https://carch-api.vercel.app/api/auth/oauth/kakao/callback/
```

앱 안으로 최종 복귀하는 주소는 백엔드 OAuth state가 관리하므로, 카카오의 Redirect URI에는 백엔드 콜백만 등록한다.

## 참고 공식 문서

- Apple App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- Apple account deletion guidance: https://developer.apple.com/support/offering-account-deletion-in-your-app/
- App Store Connect privacy: https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy/
