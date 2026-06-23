# Carch Vue Front

Carch는 카드 사용 내역, 예산, 목표 지출 계획, 커뮤니티, AI 상담을 한 흐름으로 다루는 카드 소비 관리 프론트엔드입니다. 현재 저장소는 Vue 3 + Vite 기반 모바일 앱형 UI를 기준으로 합니다.

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
npm run build    # 프로덕션 빌드 검증
npm run preview  # 빌드 결과 미리보기
```

## API

프론트는 기본적으로 `http://127.0.0.1:8000` 백엔드를 호출합니다. 다른 API 서버를 사용할 때는 `.env`에 아래 값을 설정하세요.

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

백엔드가 연결되지 않은 상태에서도 발표와 UI 확인이 가능하도록 주요 화면은 mock/fallback 데이터를 표시합니다.

## Main Routes

- `/cards`: 카드 지갑 홈, 카드 캐러셀, 최근 거래
- `/transactions`: 거래내역 목록
- `/transactions/new`: AI 입력 보정 기반 소비내역 추가
- `/budget`: 예산 및 큰 지출 관리
- `/plans`: 목표 지출 계획
- `/analytics/cards`: 카드 소비 분석
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
  card-images/     card image assets
```

## Collaboration Notes

- `node_modules`, `dist`, local logs, local env files are ignored.
- Generated reference bundles that are not used by the Vue entry are ignored to keep the repo focused.
- Run `npm run build` before sharing a PR or merge request.
