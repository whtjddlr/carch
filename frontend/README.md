# Carch Vue Front

Carch는 카드 사용 내역, 예산, 목표 지출 계획, 커뮤니티, AI 상담을 한 흐름으로 다루는 카드 소비 관리 프론트엔드입니다. 현재 저장소는 Vue 3 + Vite 기반 모바일 앱형 UI를 기준으로 합니다.

## Live URLs

- 서비스 웹: https://carch.vercel.app
- 서비스 API: https://carch-api.vercel.app
- 시연/demo 웹: https://carch-demo.vercel.app/demo
- 시연/demo API: 프론트 mock/데모 채널 기준. 별도 demo 백엔드를 붙일 때만 `BACKEND_URL_DEMO`를 설정합니다.
- legacy frontend alias: https://carch-web.vercel.app

`carch.vercel.app`은 App Store/service 기준 채널입니다. `carch-demo.vercel.app`은 포트폴리오/발표용 시연 채널이며 `/demo`와 자동 로그인 흐름을 유지합니다.

## Tech Stack

- Vue 3
- Vue Router
- Vite
- Axios
- lucide-vue-next

## Getting Started

```bash
npm install
npm run dev
```

기본 개발 서버는 Vite 설정에 따라 `http://127.0.0.1:5173`에서 실행됩니다.

## Scripts

```bash
npm run dev      # 개발 서버 실행
npm run dev:mock # 백엔드 없이 mock 데이터로 개발 서버 실행
npm run build    # 프로덕션 빌드 검증
npm run ios:sync # iOS 앱용 웹 빌드 후 Capacitor 동기화
npm run ios:open # Xcode 프로젝트 열기
npm run preview  # 빌드 결과 미리보기
```

## API

개발 환경에서는 기본적으로 `http://127.0.0.1:8000` 백엔드를 호출합니다. Vercel 프로덕션 배포에서는 same-origin `/api/...`를 호출하고 `api/proxy.js` 프록시가 `BACKEND_URL`로 전달합니다.

```bash
BACKEND_URL=http://127.0.0.1:8000
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Vercel 프론트 프로젝트에서는 아래처럼 설정하면 브라우저가 프론트 도메인의 `/api`만 호출합니다.

```bash
BACKEND_URL=https://<backend-vercel-domain>
BACKEND_URL_DEMO=https://<demo-backend-vercel-domain>
BACKEND_URL_SERVICE=https://<service-backend-vercel-domain>
VITE_API_BASE_URL=
VITE_DEMO_HOSTS=carch-demo.vercel.app
VITE_SERVICE_HOSTS=carch.vercel.app,carch-service.vercel.app
```

같은 프론트 배포에 여러 alias를 붙일 때는 host 기준으로 채널을 나눕니다. `carch-demo.vercel.app`은 demo 채널로 동작해 `/demo`와 `카치 바로 시작`을 노출하고, `carch.vercel.app`은 service 채널로 동작해 demo-only 진입점과 소셜/아이디 기반 시연 힌트를 숨깁니다. 커뮤니티는 service 채널에도 포함하며, 신고/숨김/작성자 삭제 흐름을 유지합니다.

카드 이미지는 demo 채널에서만 유지합니다. service/App Store 빌드는 카드 이미지 URL을 렌더링하지 않고, 빌드 산출물에서도 실카드 이미지 파일을 제거합니다. service 번들에는 CARCH 자체 캐릭터 이미지(`magpie-face*.png`)만 남깁니다.

백엔드 없이 UI와 플로우만 검수할 때는 mock 모드를 사용합니다.

```bash
npm run dev:mock
```

mock 모드는 `VITE_USE_MOCK_API=true`로 실행되며 카드, 거래, 검색, 소비 분석, 카드 추천, 카치 채팅, 커뮤니티, 소비계획 데이터를 프론트에서 직접 반환합니다. 디자이너/프론트 담당자는 백엔드 설치 없이 `http://127.0.0.1:5175`에서 전체 화면을 확인할 수 있습니다.

## iOS App Shell

Capacitor 기반 iOS 프로젝트는 `ios/`에 생성되어 있습니다.

```bash
npm run ios:sync
npm run ios:open
```

앱스토어용 service 빌드는 반드시 service 백엔드 API를 직접 호출해야 합니다. `VITE_IOS_API_BASE_URL`을 지정하지 않으면 `ios:sync`가 실패합니다.

```bash
VITE_IOS_API_BASE_URL=https://<service-backend-vercel-domain> npm run ios:sync
```

현재 service API 기준 명령:

```bash
VITE_IOS_API_BASE_URL=https://carch-api.vercel.app npm run ios:sync
```

로컬에서 iOS 껍데기만 임시 확인할 때도 mock API가 아니라 service API를 지정해 실제 로그인/계정 삭제 흐름을 검증합니다.

## Main Routes

- `/cards`: 카드 지갑 홈, 카드 캐러셀, 최근 거래
- `/transactions`: 거래내역 목록
- `/transactions/new`: AI 입력 보정 기반 소비내역 추가
- `/budget`: 예산 및 큰 지출 관리
- `/plans`: 목표 지출 계획
- `/analytics`: 카드 소비 분석
- `/community`: 카드 후기 커뮤니티
- `/chat`: AI 카드 상담
- `/settings`: 설정

## Project Structure

```text
src/
  components/      reusable Vue components
  composables/     purchase-plan state and helpers
  data/            mock data and formatting helpers
  router/          route definitions
  services/        API clients
  styles/          global app/theme styles
  views/           page-level Vue views
public/
  card-images/     demo card image assets and CARCH-owned magpie assets
```

## Collaboration Notes

- `node_modules`, `dist`, local logs, local env files are ignored.
- Generated reference bundles that are not used by the Vue entry are ignored to keep the repo focused.
- Run `npm run build` before sharing a PR or merge request.
