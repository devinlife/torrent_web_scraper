# UI 디자인 사양 (2026-10-18)

대상: dev 서버(`127.0.0.1:8081`)의 `/`, `/programs`, `/sites`, `/runs/1`, 그리고 템플릿 7개.
사용자는 한 명이다. 가끔 열어서 (A) 크롤링 상태와 받은 것을 확인하고, (B) 프로그램을 추가하거나 지우고, (C) 고장난 사이트를 고친다.
`ux-review.md`의 동작 개선(확인 창, 한국어 라벨, 상대 시각, flash)은 이미 반영돼 있다. 이 문서는 **보이는 모습**과, 그에 딸린 작은 흐름 변경만 다룬다.
`research-ui.md`의 "라이브러리 없이 CSS 66줄" 결론은 제품 책임자가 받아들이지 않았다. 이 문서는 그 결론을 대체한다.

## 0. 지금 화면의 문제 (스크린샷 확인)

- 앱 셸이 없다. nav는 링크 세 개와 밑줄뿐이고, 본문과 같은 흰 바탕 위에 떠 있다. 브랜드도, 면 구분도 없다.
- 표가 1990년대 모양이다. 모든 칸에 테두리가 있고, 행 높이는 24px, 머리행만 회색이다. 프로그램 표 17행이 엑셀 격자처럼 보인다.
- 버튼은 브라우저 기본 회색 버튼이다(`끄기`, `저장`, `진단`). primary 하나만 색이 있다.
- 대시보드의 상태, 다음 실행, 주기 폼, 지금 실행이 본문 글자 크기로 위아래에 흩어져 있다. 2초 안에 "괜찮은가"를 읽을 덩어리가 없다.
- 사이트 화면은 4칸 표 안에 이름, URL, `▶ 수정`, 토글 버튼, 진단 버튼이 모두 들어가 있다. 칸마다 높이와 기준선이 어긋난다.
- 간격 체계가 없다. h1, 문단, 폼, 표 사이 간격이 브라우저 기본 margin이다.

## 1. 조사 요약

| 주제 | 관례 | 이 앱에 적용 |
|---|---|---|
| 앱 셸 | Tailwind UI의 "stacked" 셸: 전체 폭 상단 바(브랜드 + 가로 nav + 오른쪽 보조 영역), 아래에 페이지 머리(제목 + 오른쪽 동작), 그 아래 본문 [1][2] | 화면이 3개뿐이라 사이드바 대신 stacked 상단 바를 쓴다. 환경 배지는 상단 바 오른쪽에 둔다 |
| 페이지 머리 | "Page heading with actions": 왼쪽 제목과 부제, 오른쪽에 그 화면의 primary 동작 [2] | 대시보드 `지금 실행`, 사이트 `진단 모델`, 실행 상세 `← 대시보드`를 이 자리에 둔다 |
| 상태 우선 | Healthchecks 대시보드는 체크마다 상태(up/late/down), 마지막 ping, 다음 예상 시각을 나란히 보인다. 색은 초록/주황/빨강 [3][4]. Uptime Kuma는 상태색 막대와 가동률을 카드에 둔다 [5] | 상태 히어로 카드에 "마지막 실행 결과 + 상대 시각"과 "다음 실행 + 남은 시간"을 나란히 둔다. 색 매핑은 지금 것을 유지한다 |
| 통계 타일 | Plausible은 머리 숫자 여러 개를 한 줄로 두고, 숫자는 크게, 라벨은 작게, 숫자 폭을 고정한다 [6] | 타일 4개를 한 줄로 둔다. 숫자는 30px `tabular-nums`, 라벨은 13px muted |
| 표 | 세로 테두리는 행 비교를 방해하니 쓰지 않는다. 행 사이 가로선 하나, 숫자는 오른쪽 정렬과 tabular 숫자, 머리도 같은 정렬. hover는 켠다. 줄무늬는 큰 표에만 [7][8][9] | 세로선 없음, 행 구분선 1px, hover 배경, 머리행은 작은 글자와 muted 색, 줄무늬 없음 |
| 버튼 위계 | 화면이나 컨테이너마다 primary는 하나다. secondary는 테두리, tertiary는 글자만, destructive는 다른 동작과 떨어뜨리고 눈에 덜 띄게 한다 [10][11][12] | primary / secondary / ghost / danger 4종. 삭제는 ghost-danger(빨간 글자, 배경 없음)로 두고 행 맨 끝에 둔다 |
| 다크 모드 | 순수한 검정을 쓰지 않는다. 높은 면일수록 밝게 만들어 높이를 표현한다(그림자 대신) [13]. 테두리는 다크에서 따로 정한다 [14] | 배경 `#0f1115` < 카드 `#16181d` < 보조면 `#1d2026`. 그림자는 라이트에만 쓴다 |
| 색 단계 | Radix: 1–2 배경, 3–5 컴포넌트 면, 6–8 테두리, 9–10 solid, 11–12 글자 [15]. shadcn: 쌍 토큰(`--card`/`--card-foreground`), `--border`, `--input`, `--ring` [14] | 토큰 이름은 shadcn처럼 역할로 짓는다(`--bg`, `--surface`, `--border`, `--ring`). 단계 수는 이 앱에 필요한 만큼만 둔다 |
| 밀도 | Linear는 정보 밀도는 유지하면서 시각적 잡음(아이콘, 선)을 줄였다. 색은 LCH처럼 지각 균일한 공간에서 만든다 [16] | 행 높이 44px, 글자 14px. 아이콘은 거의 쓰지 않는다. 회색은 약간 푸른 중성색으로 통일한다 |
| 참고 앱 | Sonarr v4와 Radarr는 자체 다크 테마를 갖췄다 [17]. Transmission 4 웹 UI는 jQuery 없이 다시 썼고 모바일과 다크 모드를 지원한다(gzip 68K) [18]. Gitea/Forgejo 관리 화면은 상자 사이 간격을 flex로 정리하고 폭을 넓혔다 [19] | 셀프호스팅 도구에서도 다크 모드와 모바일은 기본이 됐다. 빌드 없는 손 CSS로 충분하다 |
| Pico CSS 2 기본값 | 라운드 0.25rem, 폼 패딩 0.75rem×1rem, 간격 기본 1rem, 루트 글자 크기를 화면 폭에 따라 키운다 [20][21] | 프레임워크로 쓰지는 않는다. 폼 높이와 패딩만 참고해서 조금 더 촘촘하게 잡는다(36px, 8px×12px) |
| 포커스 | WCAG 2.4.13(AAA): 2px 이상 실선, 주변 색과 3:1 이상 [22] | `outline: 2px solid var(--ring); outline-offset: 2px`를 모든 대화형 요소의 `:focus-visible`에 준다 |

## 2. 기술 결정

**직접 만든 디자인 시스템 하나: `app/static/app.css`(약 400줄). 프레임워크는 쓰지 않는다. Pretendard Variable 웹폰트를 CDN으로 불러오고, 시스템 폰트를 대비책으로 둔다.**

1. 화면 6개, 컴포넌트 12개로 범위가 작고 정해져 있다. 프레임워크를 쓰면 덮어쓰는 CSS가 더 길어진다(Pico 충돌은 `research-ui.md` §1에서 확인했다).
2. 토큰은 `:root`의 CSS 변수로 둔다. 다크 모드는 `@media (prefers-color-scheme: dark)` 안에서 같은 변수를 다시 정의한다. `light-dark()`보다 값이 한눈에 보인다.
3. `color-scheme: light dark`는 유지한다. 스크롤바, 날짜 입력, 체크박스를 브라우저가 맞춰 준다.
4. 파일을 분리한다. 줄 수가 150을 넘고 6개 화면이 공유하므로, 캐시와 편집 편의 면에서 이득이다. `app.mount("/static", StaticFiles(...))`는 Starlette 내장이라 의존성이 늘지 않는다.
5. 클래스 이름은 컴포넌트 단위로 짧게 짓는다(`.card`, `.btn`, `.badge`). 유틸리티 클래스는 `.muted`, `.num`, `.stack` 몇 개만 둔다.
6. 빌드 단계는 없다. Node, PostCSS, Tailwind를 쓰지 않는다. 저장하면 `--reload`가 바로 반영한다.
7. 웹폰트는 Pretendard Variable 하나만 쓴다. 한글 글리프가 크고 고르며, 숫자 폭이 일정하다. 불러오지 못하면 Apple SD Gothic Neo로 대체되므로 화면이 깨지지 않는다.
8. 아이콘은 글자로 충분하지 않은 곳(외부 링크 ↗, 접기 ▸)에만 쓴다. 문자나 인라인 SVG로 넣고, 아이콘 라이브러리는 쓰지 않는다.
9. JS는 htmx(doctor 폴링)와 `confirm()`만 쓴다. 토글, 접기, 확인은 모두 form POST와 `<details>`로 처리한다.
10. 캐시 무효화는 `app.css?v={{ CSS_V }}`로 한다. `CSS_V`는 파일 mtime을 템플릿 전역 변수로 넣은 값이다(views.py 한 줄).

## 3. 토큰

### 3.1 색

| 토큰 | 라이트 | 다크 | 용도 |
|---|---|---|---|
| `--bg` | `#f6f7f9` | `#0f1115` | 페이지 바탕 |
| `--surface` | `#ffffff` | `#16181d` | 카드, 상단 바, 표 |
| `--surface-2` | `#f1f3f6` | `#1d2026` | 표 머리, hover, pre, 입력 비활성 |
| `--border` | `#e3e6eb` | `#2a2e36` | 카드 테두리, 행 구분선 |
| `--border-strong` | `#cdd2da` | `#3a3f49` | 입력과 secondary 버튼 테두리 |
| `--text` | `#16181d` | `#e7e9ee` | 본문 |
| `--text-2` | `#4b5260` | `#a8afbd` | 보조 글자, 표 머리 |
| `--text-3` | `#646b78` | `#858c9a` | 라벨, 시각, 꺼진 행 (흰 바탕 5.4:1, `--surface-2` 4.8:1, 다크 카드 5.2:1) |
| `--accent` | `#2563eb` | `#2563eb` | primary 버튼 배경, 선택된 nav (다크도 같은 값: 흰 글자 5.2:1. `#3b82f6`은 3.7:1이라 탈락) |
| `--accent-fg` | `#ffffff` | `#ffffff` | primary 버튼 글자 |
| `--accent-hover` | `#1d4ed8` | `#1d4ed8` | primary hover |
| `--link` | `#1d5bd6` | `#7aa7ff` | 링크 |
| `--ring` | `#2563eb` | `#7aa7ff` | 포커스 링 |
| `--ok` / `--ok-bg` | `#147a3a` / `#e6f6ea` | `#4ade80` / `#10291a` | 정상, 완료 |
| `--warn` / `--warn-bg` | `#a15c07` / `#fdf3dc` | `#fbbf24` / `#30240b` | 일부 실패, 도메인 이전, 오래된 성공 |
| `--bad` / `--bad-bg` | `#b42318` / `#fdeceb` | `#f87171` / `#351517` | 실패, 차단, 다운, 파서 고장, 삭제 |
| `--info` / `--info-bg` | `#1d4ed8` / `#e8effd` | `#7aa7ff` / `#15233d` | 실행 중, 안내 flash |
| `--env` / `--env-bg` | `#6d28d9` / `#efe9fd` | `#c4b5fd` / `#261c45` | DEV 배지, dry-run 띠 |

- 상태색은 "글자색 + 옅은 배경" 쌍으로만 쓴다. 상태를 색만으로 전하지 않는다. 배지에는 항상 글자가 있다.
- `--accent`(파랑)와 `--info`(파랑)는 같은 계열이다. 실행 중은 "진행"이라 따로 구분할 이유가 약하다. 보라는 DEV만 쓴다.

### 3.2 글자

```css
--font: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui,
        "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif;
--mono: ui-monospace, "SF Mono", Menlo, "D2Coding", Consolas, monospace;
```

| 토큰 | 크기 / 줄높이 / 굵기 | 용도 |
|---|---|---|
| `--fs-xs` | 12 / 16 / 600 | 배지, 표 머리(대문자 없음) |
| `--fs-sm` | 13 / 18 / 400 | 라벨, 시각, 보조 문구, pre |
| `--fs-base` | 14 / 20 / 400 | 본문, 표, 버튼, 입력 |
| `--fs-md` | 16 / 24 / 600 | 카드 제목 |
| `--fs-lg` | 20 / 28 / 700 | 상태 히어로 문장 |
| `--fs-xl` | 24 / 32 / 700 | 페이지 제목 (`letter-spacing: -0.01em`) |
| `--fs-stat` | 30 / 36 / 700 | 통계 타일 숫자 (`tabular-nums`) |

- `body { word-break: keep-all; -webkit-font-smoothing: antialiased; }`. 숫자 칸은 `font-variant-numeric: tabular-nums`.

**폰트 결정: Pretendard Variable 1.3.9, 가변 동적 서브셋을 jsDelivr에서 불러온다.**

```html
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" crossorigin="anonymous"
      href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css"
      integrity="sha384-2nNKoOPayicGa+aRguOQuiZP+RqQ4G3jalfDeOgftkKD7zBM2gJXTwcFqCZltdv0">
```

- 1.3.9가 jsDelivr의 최신 버전이다(`data.jsdelivr.com` 확인). 2026-10-18에 HTTP 200, 59.9 KB를 확인했고 SRI는 직접 계산했다.
- `.min.css`가 아니라 `.css`를 쓴다. jsDelivr의 `.min.css`는 요청할 때 만들어지는 파일이라 SRI를 붙이지 말라고 파일 안에 적혀 있다. 원본 `.css`는 고정 파일이다.
- 동적 서브셋이라 화면에 나온 글자가 속한 woff2 조각만 받는다. `font-display: swap`이 들어 있어서 첫 표시가 늦어지지 않는다.
- 시스템 폰트만 쓰는 방안과 비교했다. Mac의 Apple SD Gothic Neo도 읽기에는 문제없다. 다만 가변 굵기(45–920)를 쓸 수 없고, 숫자와 라틴 글자의 기준선과 폭이 한글과 따로 놀아서 통계 숫자와 표 숫자가 덜 정돈돼 보인다. 그래서 웹폰트를 쓴다.
- 외부 요청이 하나 늘어난다. 하지만 이 앱은 이미 htmx를 unpkg에서 받고 있어서 새로운 종류의 의존은 아니다. 오프라인이면 시스템 폰트로 대체된다.
- 대안 경로(cdnjs, 고정 min 파일): `https://cdnjs.cloudflare.com/ajax/libs/pretendard/1.3.9/variable/pretendardvariable-dynamic-subset.min.css`, `sha384-yrRxb1ijbFpccVLlUyFKO/3aN/HZkRi3ayQm7YC2u7nEh6IvE0mohDVEDepTertg`.

### 3.3 간격, 라운드, 그림자, 크기

- 간격(4px 기준): `--s-1 4px`, `--s-2 8px`, `--s-3 12px`, `--s-4 16px`, `--s-5 20px`, `--s-6 24px`, `--s-8 32px`, `--s-10 40px`.
  - 카드 안쪽 여백 20px(모바일 16px), 카드 사이 16px, 섹션 사이 32px, 폼 필드 사이 12px.
- 라운드: `--r-sm 6px`(버튼, 입력, 배지 외), `--r-md 10px`(카드), `--r-full 999px`(배지, 스위치).
- 그림자(라이트만): `--shadow-1: 0 1px 2px rgb(16 24 40 / .06)`(카드), `--shadow-2: 0 4px 12px rgb(16 24 40 / .08)`(펼친 편집기). 다크에서는 `none`으로 두고 면 밝기와 테두리로 높이를 표현한다.
- 컨트롤 높이: 36px(기본), 28px(`.btn-sm`, 표 안). 표 행 최소 44px. 콘텐츠 최대 폭 1120px, 좌우 여백 24px(모바일 16px).
- 브레이크포인트 하나: `@media (max-width: 720px)`.

## 4. 컴포넌트

| 컴포넌트 | 마크업 | 스타일 요점 |
|---|---|---|
| 상단 바 | `<header class="topbar"><div class="wrap"><a class="brand">` + `<nav>` + `.env` | 높이 56px, `--surface`, 아래 1px `--border`, `position: sticky; top: 0`. 브랜드는 `■ torrent`(■는 `--accent` 8px 사각형, CSS). nav 링크는 32px 높이의 알약 모양: 기본 `--text-2`, hover `--surface-2`, `aria-current` 배경 `--surface-2` + 글자 `--text` 600 |
| dry-run 띠 | dev에서 상단 바 바로 아래 `<div class="envbar">` | 높이 28px, `--env-bg` 바탕, `--env` 13px 글자: "DEV · dry-run — Transmission 추가, 다운로드 기록, URL 변경을 하지 않습니다". 모든 화면에 보이므로 대시보드의 muted 문장은 지운다 |
| 페이지 머리 | `<div class="page-head"><div><h1>` + `<p class="sub">` + `</div><div class="actions">` | flex, `justify-content: space-between; align-items: end`, 아래 여백 24px. 모바일에서는 세로로 쌓고 actions를 전체 폭으로 |
| 카드 | `<section class="card">`, 머리는 `<header class="card-head"><h2>` + 오른쪽 링크·버튼 | `--surface`, 1px `--border`, `--r-md`, `--shadow-1`. 표를 담으면 안쪽 여백 0이고 표가 카드 모서리까지 닿는다(`overflow: hidden`) |
| 상태 히어로 | `.card.hero.is-ok|is-warn|is-bad|is-run|is-none` | 왼쪽 4px 상태색 띠(`border-left`), 큰 문장 20px, 아래 13px 메타 줄. 오른쪽에 "다음 실행" 블록과 primary 버튼. 아래 구분선 아래에 주기 폼 |
| 통계 타일 | `<div class="stats"><div class="stat"><dt>` 라벨 `<dd>` 숫자 + `<small>` 보조 | `grid-template-columns: repeat(4, 1fr)`, 모바일 2열. 타일은 카드 스타일, 안쪽 16px. 이상 값이면 숫자에 상태색 |
| 표 | `<div class="table-wrap"><table class="table">` | `border-collapse: collapse`, 세로선 없음. `th` 12px 600 `--text-2`, 바탕 `--surface-2`, 아래 1px `--border`. `td` 위아래 10px, 좌우 16px, 아래 1px `--border`, 마지막 행 선 없음. `tbody tr:hover { background: var(--surface-2) }`. `.num` 오른쪽 정렬 + tabular. `tr.off td { color: var(--text-3) }`. 긴 제목은 `.truncate`(한 줄, 말줄임, `title`에 원문). 모바일에서는 `.hide-sm` 칸을 숨긴다 |
| 버튼 | `<button class="btn btn-primary|btn-secondary|btn-ghost|btn-danger [btn-sm]">` | 36px, 패딩 0 14px, 14px 600, `--r-sm`, `inline-flex; gap 6px; white-space: nowrap`. primary: `--accent` 바탕. secondary: `--surface` 바탕 + `--border-strong` 테두리. ghost: 투명, hover `--surface-2`. danger: 투명, `--bad` 글자, hover `--bad-bg`. `:disabled` 투명도 .5. **class 없는 `<button>`은 쓰지 않는다** |
| 배지 | `<span class="badge ok" title="ok"><i></i>정상</span>` (매크로 수정) | 22px 알약, 12px 600, 패딩 0 8px, 상태 쌍 색. `<i>`는 6px 점(`background: currentColor`, CSS만). `running`의 점은 `@keyframes` 1.5초 깜빡임, `prefers-reduced-motion`에서 멈춤 |
| 켜기/끄기 스위치 | form POST 하나에 `<button class="switch" role="switch" aria-checked="true" aria-label="놀면 뭐하니 끄기">` | 36×20 트랙(`--r-full`), 켜짐 `--ok`, 꺼짐 `--border-strong`, 16px 흰 손잡이. 누르면 POST하고 다시 그린다. 상태 글자("켜짐/꺼짐")는 옆에 13px로 함께 둔다. JS 없이 진짜 스위치처럼 보인다 |
| 폼 필드 | `<label class="field"><span>라벨</span><input class="input">` + `<small class="hint">` | 라벨은 위에 13px 600 `--text-2`, 간격 6px. 입력 36px, 패딩 0 12px, `--surface` 바탕, 1px `--border-strong`, `--r-sm`. focus 시 테두리 `--ring` + `box-shadow: 0 0 0 3px` 옅은 ring. `select`는 `appearance: none` + CSS 삼각형. 한 줄 폼은 `.form-row`(flex, `align-items: end`, gap 12px, 모바일에서 세로) |
| 인라인 편집기 | `<details class="editor"><summary class="btn btn-ghost btn-sm">수정</summary><form class="editor-body">` | summary 기본 삼각형을 숨기고 버튼처럼 보인다. 열리면 summary 글자가 "닫기"로 바뀐다(CSS `details[open] > summary` + `::after`). 본문은 `--surface-2` 바탕, 16px 여백, 위 1px 선, 오른쪽 아래에 [취소(ghost, summary 닫기 안내)] [저장(primary)] |
| flash | `<div class="flash flash-info|flash-ok|flash-bad" role="status">` | 페이지 머리 바로 아래. 왼쪽 3px 상태색 띠, 상태 쌍 색 바탕, 14px. 오른쪽에 동작 링크(예: "지금 실행") 자리. 자동으로 사라지지 않는다. 다음 이동 때 없어지므로 닫기 버튼도 두지 않는다 |
| 빈 상태 | `<div class="empty"><p class="empty-title">` + `<p class="muted">` + 동작 | 표 대신 카드 안 가운데 정렬, 위아래 32px. 제목 14px 600, 설명 13px muted. 표의 `colspan` 한 줄보다 덜 표 같아 보여서 "고장"으로 오해하지 않는다 |
| 로그 pre | `<pre class="log">` | `--mono` 12.5px, 줄높이 1.6, `--surface-2`, 1px `--border`, `--r-sm`, 16px 여백, `max-height: 60vh; overflow: auto`. `FAIL`, `ERROR`, `error` 줄은 서버에서 `<mark class="log-bad">`로 감싸 `--bad-bg` 바탕을 준다 |
| 확인 | 지금처럼 `onsubmit="return confirm(...)"` | 모달을 만들지 않는다. 대신 버튼 문구에 결과를 쓴다: "진단 · 최대 $1", "삭제". 확인 문구도 지금 것을 유지한다 |
| 접근성 | 전체 | `:focus-visible` 2px ring, 2px offset. 버튼 최소 28px(표), 터치 화면 행 안의 대상은 36px. `prefers-reduced-motion`에서 애니메이션 없음 |

## 5. 화면별 와이어프레임

### 5.1 공통 셸

```
desktop ≥960                                                         phone 390
┌────────────────────────────────────────────────────────────────┐   ┌──────────────────────────┐
│ ■ torrent   [대시보드] 프로그램  사이트                 DEV   │   │ ■ torrent           DEV │
├────────────────────────────────────────────────────────────────┤   │ [대시보드] 프로그램 사이트│ ← nav는 둘째 줄, 가로 스크롤 없이 3개
│ DEV · dry-run — Transmission 추가, 기록, URL 변경을 하지 않음  │   ├──────────────────────────┤
└────────────────────────────────────────────────────────────────┘   │ DEV · dry-run — …        │
                                                                     └──────────────────────────┘
```
- 모바일 nav: 햄버거를 쓰지 않는다. 링크가 3개뿐이라 둘째 줄에 고르게 펼친다(`flex: 1`, 가운데 정렬, 40px 높이). 상단 바 전체가 sticky다.

### 5.2 대시보드 `/`

```
┌ 대시보드 ──────────────────────────────────────────── [▶ 지금 실행] ┐  ← page-head, primary
│ 60분마다 자동으로 확인합니다                                        │
├─ flash-info: 실행을 시작했습니다. 10초마다 새로 고칩니다. ──────────┤  (msg=started일 때)
┌────────────────────────────────────────────────────────────────────┐
┃ ● 정상                                    다음 실행                 │  ← hero.is-ok, 왼쪽 띠 초록
┃ 마지막 실행 20:11 · 14분 전                21:11 · 45분 후          │     20px 문장 / 우측 16px
┃ 매칭 3 · 추가 0 · 33초 · 로그 보기 →                                │     13px 메타
┃ ──────────────────────────────────────────────────────────────────  │
┃ 주기  [ 60 ] 분  [저장]                                             │  ← secondary 버튼
└────────────────────────────────────────────────────────────────────┘
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│ 24시간 추가   ││ 최근 실행     ││ 사이트        ││ 프로그램      │
│ 0            ││ 9/10 정상     ││ 3/3 정상      ││ 2 켜짐        │
│ 최근 20건 중  ││ 최근 10회     ││ 켜진 사이트   ││ 전체 17       │
└──────────────┘└──────────────┘└──────────────┘└──────────────┘
┌ 최근 실행 ──────────────────────────────────────────────────────────┐
│  #   시작          소요      상태        매칭   추가                │
│  2   20:11         33초      ● 정상         3      0                │
│  1   10-18 19:23   12분 30초 ● 실패         0      0                │
└────────────────────────────────────────────────────────────────────┘
┌ 다운로드 ───────────────────────────────────────────────────────────┐
│  추가 시각   프로그램      회차           제목                 사이트│
│  ……  (없으면 empty: "아직 받은 회차가 없습니다" / dev: "dev는 기록하지 않습니다")│
└────────────────────────────────────────────────────────────────────┘

phone 390
┌ 대시보드 ──────────────┐
│ [▶ 지금 실행 ─ 전체 폭]│
┃ ● 정상                 │
┃ 20:11 · 14분 전        │
┃ 매칭 3 · 추가 0 · 로그→│
┃ 다음 21:11 · 45분 후   │
┃ 주기 [60]분 [저장]     │
├───────────┬────────────┤
│ 24h 추가 0│ 실행 9/10  │  ← 2열
│ 사이트 3/3│ 프로그램 2 │
├────────────────────────┤
│ #  시작  상태    추가  │  ← 소요·매칭 .hide-sm
│ 시각  프로그램  회차   │  ← 다운로드는 제목·사이트 .hide-sm, 제목은 행 아래 13px 줄로
└────────────────────────┘
```

히어로 상태 규칙(위에서부터 첫 번째가 이긴다):

| 조건 | 클래스 | 문장 |
|---|---|---|
| `running` | `is-run` | ● 실행 중 · 시작 20:11 |
| 실행 기록 없음 | `is-none` | 아직 실행하지 않았습니다 |
| `last.status == error` | `is-bad` | ● 실패 + 메타 줄 끝에 `사이트 확인 →` |
| `partial` 또는 켜진 사이트 중 오래된 성공이 있음 | `is-warn` | ● 일부 실패 / ● 정상 · 사이트 1곳 응답 없음 |
| 그 밖 | `is-ok` | ● 정상 |

- "다음 실행" 블록: `running`이면 "실행 중", `due`이면 "곧 실행", 그 밖은 `21:11` + `45분 후`. 카운트다운은 서버 렌더 값이다. 실행 중이 아니어도 `<meta refresh content="60">`을 넣어 1분마다 다시 그린다(JS 없음).
- 통계 타일(새 DB 쿼리 없이 이미 있는 함수로):
  - **24시간 추가**: `downloads`(이미 20건을 받는다) 중 `added_at`이 24시간 안인 수. 20건 모두 해당하면 `20+`. 아래 줄은 "최근 20건 기준".
  - **최근 실행**: `runs[:10]` 중 `ok` 수 / 개수. 8 미만이면 `--warn`, 0이면 `--bad`.
  - **사이트**: `db.list_sites(conn, enabled_only=True)`에서 `last_ok_at`이 기준(주기의 3배) 안인 수 / 켜진 수. dev에서는 `last_ok_at`이 갱신되지 않으니 "dev는 집계하지 않음"으로 쓴다. 타일 전체가 `/sites` 링크다.
  - **프로그램**: `db.list_programs(conn, enabled_only=True)`의 길이, 아래 줄에 전체 수(`len(list_programs)`는 17행이라 그냥 부른다). 타일 전체가 `/programs` 링크다.
- 표: 실행 `#`은 링크, 상태는 점 배지, `추가 > 0`이면 굵게 `--ok`. 다운로드 제목은 `.truncate` + `title`.

### 5.3 프로그램 `/programs`

```
┌ 프로그램 ────────────────────────────────────────────────────────────┐
│ 켜짐 2 · 전체 17 · 위에 있을수록 먼저 매칭됩니다                    │
├ flash-bad: 이미 있는 이름입니다: 라디오스타 ─────────────────────────┤
┌ 새 프로그램 ─────────────────────────────────────────────────────────┐
│ 이름                         해상도                                  │
│ [예: 놀면 뭐하니           ] [ ]720p [ ]1080p   [+ 추가]            │  ← form-row, fieldset.checks, primary
│ 제목에 … 해상도를 고르지 않으면 무관입니다. 여러 개 고르면 …         │  ← hint
└──────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────┐
│ 순서  이름             해상도           켜기                         │
│  1    라디오스타        [무관 ▾]        (●━) 켜짐             삭제   │  ← 삭제는 btn-danger btn-sm, 맨 오른쪽
│  2    PD 수첩           [720p · 1080p ▾](━○) 꺼짐             삭제   │  ← tr.off: 글자 --text-3
│                         [x]720p [x]1080p [저장]                      │  ← 펼친 details.res-edit: 같은 칸 안
│  …                                                                   │
└──────────────────────────────────────────────────────────────────────┘

phone 390
┌ 프로그램 ──────────────┐
│ 켜짐 2 · 전체 17       │
│ 이름 [_______________] │
│ 해상도 [ ]720p [ ]1080p│
│ [+ 추가 ─── 전체 폭]   │
├────────────────────────┤
│ 라디오스타 [무관▾] (●━) 삭제│  ← 순서는 .hide-sm, 스위치 옆 켜짐/꺼짐 글자도 숨김. 해상도 칸은 폰에서도 수정 가능
└────────────────────────┘
```
- **해상도 칸**: 값(`무관` 또는 `720p · 1080p`)이 곧 `btn-ghost btn-sm` 버튼인 `<details class="res-edit">`다. 펼치면 같은 칸 안에 체크박스와 저장이 나온다. `.table-wrap`이 잘라 먹으므로 절대 위치 팝오버는 쓰지 않는다. 닫힌 행은 44px를 유지한다. 저장하면 flash "해상도를 바꿨습니다."
- **해상도 값**: 둘 다 고른 것과 무관은 다르다. 둘 다 고르면 해상도 표기가 없는 제목은 받지 않는다.
- **정렬과 묶음**: 데이터 순서는 바꾸지 않는다. 순서가 곧 매칭 우선순위이고, 켜짐을 위로 올리면 사용자가 "위가 우선"이라는 규칙을 잘못 읽는다. 시각적인 묶음(켜짐 섹션/꺼짐 섹션)도 하지 않는다. 같은 이유로 우선순위가 두 표에 나뉘어 보인다. 대신 꺼진 행을 흐리게 하고(`tr.off`), 켜진 행의 이름을 600 굵기로 해서 17개 중 2개가 바로 보이게 한다. 부제에 "위에 있을수록 먼저 매칭됩니다"를 쓴다.
- 꺼진 프로그램이 많아지면 `<details>`로 "꺼진 프로그램 15개"를 접는 방안이 있다. 지금은 17행이라 하지 않는다.
- 빈 상태: "아직 프로그램이 없습니다 / 위에서 이름을 넣고 추가하세요".

### 5.4 사이트 `/sites`

```
┌ 사이트 ───────────────────────────────────────── 진단 모델 [sonnet ▾][저장] ┐  ← actions 자리, secondary
│ 켜진 3곳 · 최근 성공이 180분 넘게 없으면 경고합니다                        │
├ flash-ok: 토렌트썸 설정을 바꿨습니다. 다음 실행에서 확인됩니다. [지금 실행]┤
┌──────────────────────────────────────────────────────────────────────────┐
│ 토렌트썸              최근 성공            최근 진단          (●━) 켜짐  │  ← .site-row: 정체 · dl 2열 · 컨트롤
│ torrentsome268.com ↗  10-18 20:11 · 14분 전 ● 정상 · 2일 전 → [진단 · 최대 $1]│  ← 링크 13px 새 탭, 라벨 12px muted
│ ──────────────────────────────────────────────────────────────────────── │
│ [수정]                                                                   │  ← .site-foot: ghost, 편집기만
│ ┌ (열림) URL [https://torrentsome268.com                  ]            ┐ │  ← 카드 전체 폭
│ │ 게시판 경로 (한 줄에 하나)                                            │ │
│ │ [/v-4-16                                                 ]            │ │
│ │ [/v-2-13                                                 ]            │ │
│ │                                                [닫기] [저장]          │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
┌ 토렌트알지 (꺼짐 카드: 이름·사실 글자 --text-3, 스위치 꺼짐) ────────────┐
```
- 카드 목록: 모든 폭에서 1열. 카드 안을 가로 한 줄(`.site-row`: 이름·URL `minmax(0,15rem)` · 사실 `1fr` · 스위치와 진단 `auto`)로 놓아 카드가 낮고, 사이트 5곳이 한 화면에 들어온다. 아래 `.site-foot`에는 수정 편집기만 둔다.
- 최근 성공: 오래됐으면 시각 앞에 `badge warn`("응답 없음 · 5시간 전")을 두고, 카드 왼쪽 띠를 `--warn`으로 한다. dev에서는 "dev는 기록하지 않음"으로 쓴다.
- 최근 진단: 배지 + 경과 시간, 리포트로 가는 링크. 진단한 적이 없으면 "진단 기록 없음". 진단이 `running`이면 배지 "진단 중"과 "진행 보기 →"를 두고, 진단 버튼은 `disabled`로 한다.
- 진단 버튼은 secondary다. 이 화면의 primary는 없다. 진단은 돈이 드는 동작이라 강조하지 않는다. 사이트가 경고 상태일 때만 그 카드의 진단 버튼을 primary로 올린다(카드마다 primary 하나 규칙 [11]).
- 수정 편집기 저장은 지금처럼 confirm을 거친다.

phone 390: `.site-row`가 세로로 쌓인다(이름·URL → `최근 성공`/`최근 진단` 세로 → 스위치 왼쪽, [진단] 오른쪽). [수정]은 그 아래 줄.

### 5.5 실행 상세 `/runs/{id}`

```
┌ ← 대시보드 ──────────────────────────────────────────────────────────┐  ← 13px 링크, page-head 위
│ 실행 #2  ● 정상                                                      │
│ 20:11 시작 · 33초 · 매칭 3 · 추가 0                                  │
┌ 로그 ────────────────────────────────────────────── [전체 줄 1,204] ┐
│ site 토렌트썸: /v-4-16 30 posts                                      │  ← pre.log, 고정폭
│ ▓ site 토렌트좋다 FAIL timeout ▓                                      │  ← mark.log-bad
└──────────────────────────────────────────────────────────────────────┘
```
- 실패 실행이면 메타 줄 아래에 `flash-bad`를 하나 둔다: "실패한 사이트가 있습니다 · 사이트 확인 →".
- phone: 같은 구조. pre는 가로 스크롤 없이 `white-space: pre-wrap`.

### 5.6 Doctor 리포트 `/doctor/{id}`

```
┌ ← 사이트 ────────────────────────────────────────────────────────────┐
│ 진단 · 토렌트썸                                                       │
│ sonnet · 시작 20:30 (3분 전) · 비용 $0.214                           │
┌──────────────────────────────────────────────────────────────────────┐
┃ ● 도메인 이전                                                        │  ← hero, 판정색 띠(ok/warn/bad/run)
┃ torrentsome268.com이 응답하지 않고 269에서 같은 게시판이 열립니다.   │  ← summary 16px
└──────────────────────────────────────────────────────────────────────┘
┌ 수정 제안 ─────────────────────────────────── [이 설정으로 변경] ────┐  ← primary, 카드 머리 오른쪽
│          현재                         제안                           │
│ URL      torrentsome268.com           torrentsome269.com            │  ← 바뀐 칸: --ok-bg 바탕 + 600
│ 게시판   /v-4-16 /v-2-13 /v-4-17      (같음, muted)                  │
└──────────────────────────────────────────────────────────────────────┘
┌ 근거 ────────────────────────────────────────────────────────────────┐
│ • dns_tls_check: 268 TLS 실패                                         │
│ • probe_domains: 269에서 글 30개                                      │
└──────────────────────────────────────────────────────────────────────┘
▸ 진행 로그 (42줄)                                                       ← details, 끝나면 접힘
```
- 실행 중: hero는 `is-run`, 문장 "진단 중입니다 · 상한 $1", summary 자리에 "보통 1–3분 걸립니다". 진행 로그 카드는 펼쳐 둔 채 htmx가 2초마다 `pre.log`를 바꾼다(지금 동작 그대로). 끝나면 `HX-Refresh`로 전체가 다시 그려진다.
- 제안이 없으면 수정 제안 카드 대신 "현재 설정" 카드를 2행 표로 둔다(제안 칸 없음).
- `error`(구조화 출력 없음): hero `is-bad`, 문장 "진단을 끝내지 못했습니다", 로그를 펼쳐 둔다.
- phone: 비교 표는 `현재`/`제안`을 위아래로 쌓는다(`th` 행 머리 + 두 줄). 적용 버튼은 카드 아래 전체 폭.

### 5.7 오류 페이지

```
┌──────────────────────────────────────────┐
│                 404                      │  ← --fs-stat, --text-3
│      페이지를 찾을 수 없습니다.           │  ← 16px
│      [대시보드로]  [뒤로]                │  ← primary / ghost(history.back 없이 Referer 링크, 없으면 생략)
└──────────────────────────────────────────┘
```
- 카드 하나를 가운데에 두고 최대 폭 480px. 셸(상단 바)은 그대로 보여서 nav로 바로 갈 수 있다.

## 6. 흐름 변경 (모습 말고)

1. **지금 실행 뒤**: `/?msg=started` → `flash-info` "실행을 시작했습니다. 끝나면 결과가 여기에 나옵니다." hero는 `is-run`(스케줄러가 아직 lock을 안 잡았어도 `msg=started`면 실행 중으로 그린다)이고 10초 refresh. refresh URL은 `/`라서 다음 렌더에서 flash가 사라지고, 끝나면 hero가 결과 색으로 바뀐다(지금 동작 유지).
2. **진단 모델 설정**: 사이트 화면 머리 오른쪽에 둔다(지금 위치 유지, 모양만 secondary 컨트롤). 설정이 하나뿐이라 설정 화면을 만들지 않는다. 진단 버튼의 `title`에 현재 모델을 쓴다("sonnet으로 진단").
3. **주기 설정**: 대시보드 hero 안에 둔다. 저장 뒤 `flash-ok` "주기를 30분으로 바꿨습니다"를 띄운다(`go("/", msg=...)` — `go`에 `msg` 인자 하나 추가). 지금은 저장해도 아무 표시가 없다.
4. **flash 종류**: `error` → `flash-bad`, `msg` → `flash-ok` 또는 `flash-info`. 메시지 문구는 템플릿의 dict 하나(`FLASH = {"started": ..., "applied": ..., "interval": ...}`)에 모은다.
5. **적용 뒤**: `/sites?msg=applied`의 flash 안에 [지금 실행] 버튼(POST `/run-now`)을 둔다. 고친 결과를 바로 확인하는 것이 다음 행동이기 때문이다.
6. **사이트 경고에서 진단으로**: 경고 카드만 진단 버튼이 primary다. 대시보드 hero의 `사이트 확인 →`이 그 화면으로 이어진다.
7. **모바일 nav**: 둘째 줄 3분할. 햄버거 없음.
8. **삭제 위치**: 표 맨 오른쪽 끝, 스위치와 칸 하나 이상 떨어뜨린다(지금은 바로 옆 칸).

## 7. 구현 순서와 영향 범위

- `app/static/app.css` 새로 만든다(토큰 → 기본 요소 → 셸 → 컴포넌트 → 화면별 소량 → 다크 → 반응형 순).
- `app/main.py`: `app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")`, 대시보드 컨텍스트에 `sites`, `programs` 추가.
- `app/views.py`: `CSS_V` 전역, 로그 줄 강조 필터 `logmark`, `go(path, error=None, msg=None)`.
- 템플릿 7개: `base.html`의 `<style>`을 지우고 `<link>`로 바꾼다. 나머지는 클래스와 구조만 바꾼다. 라우트와 폼 action은 바꾸지 않는다.
- 테스트: 지금 pytest에는 화면 HTML을 확인하는 테스트가 없다. 새 테스트는 `logmark` 하나만 둔다(어떤 줄이 `<mark>`로 감싸지는지, 이스케이프가 유지되는지).

## 8. 의도적으로 하지 않는 것

- 테마 토글 버튼: OS 설정을 따른다. 사용자 한 명, Mac 한 대.
- 아이콘 라이브러리(Lucide, Heroicons 등): 상태 점은 CSS, 외부 링크는 ↗ 문자로 충분하다.
- 차트와 sparkline: 실행 10건, 다운로드 20건으로는 추세가 나오지 않는다. 숫자 타일로 충분하다.
- htmx와 `confirm()` 밖의 JS: 토스트, 모달, 클라이언트 카운트다운, 드래그 정렬(프로그램 순서 변경)을 만들지 않는다. 순서 변경이 필요해지면 그때 `↑↓` POST 버튼으로 한다.
- 사이드바, 설정 화면, 페이지네이션, 표 정렬·필터.
- CSS 프레임워크와 빌드 단계.
- 웹폰트 자체 호스팅: CDN이 안 되면 시스템 폰트로 대체되니, woff2를 repo에 넣지 않는다.

## 출처

1. Tailwind Plus, Application Shells – Stacked: https://tailwindcss.com/plus/ui-blocks/application-ui/application-shells/stacked
2. Tailwind Plus, Section headings (with actions): https://tailwindcss.com/plus/ui-blocks/application-ui/headings/section-headings
3. Healthchecks dashboard (status, last ping, next expected): https://github.com/healthchecks/dashboard
4. Healthchecks badges (up 초록 / late 주황 / down 빨강): https://healthchecks.verbis.dkfz.de/docs/badges/
5. Uptime Kuma 소개(상태 막대, 가동률): https://dreamserver.ro/en/blog/uptime-kuma-uptime-monitoring/
6. Plausible guided tour(머리 숫자 줄): https://docs.plausible.io/guided-tour
7. Maersk Design System – Table: https://designsystem.maersk.com/components/table/
8. Winnipeg Design System – Tables(세로선 피하기, 줄무늬): https://legacy.winnipeg.ca/designsystem/components/tables
9. Spiris Design System – Table(hover 상태): https://designsystem.spiris.se/development/documentation/docs/table/
10. Red Hat Design System – Button guidelines: https://ux.redhat.com/elements/button/guidelines/
11. Intelligence Community Design System – Button(컨테이너마다 primary): https://design.sis.gov.uk/components/inputs/button
12. Cieden – Button hierarchy(destructive 배치): https://cieden.com/book/atoms/button/how-to-create-button-hierarchy
13. Material Design 2 – Dark theme(높이 = 더 밝은 면): https://m2.material.io/design/color/dark-theme
14. shadcn 테마 토큰 해설: https://21st.dev/blog/shadcn-theming-css-variables , https://makerkit.dev/docs/tanstack-supabase/customization/theme
15. Radix Colors – Composing a palette / 단계 용도: https://www.radix-ui.com/colors/docs/palette-composition/composing-a-palette , https://pub.dev/documentation/radix_colors/latest/
16. Linear – How we redesigned the Linear UI: https://linear.app/blog/how-we-redesigned-the-linear-ui
17. Sonarr v4 release(다크 모드): https://forums.sonarr.tv/t/sonarr-v4-beta/31078
18. Transmission 4.0 release(웹 UI 재작성, 모바일, 다크): https://www.linuxuprising.com/2023/02/transmission-bittorrent-client-40.html
19. Gitea/Forgejo 설정 화면 flex 정리 커밋 기록: https://git.fb1.uni-bremen.de/davrot/forgejo_backup/commits/branch/forgejo/templates/repo/settings/navbar.tmpl
20. Pico CSS – CSS variables: https://picocss.com/docs/css-variables
21. Pico CSS 2.1.1 기본값 정리(2차 자료): https://open-design.ai/design-system/pico-css/
22. WCAG 2.2 SC 2.4.13 Focus Appearance: https://kb.daisy.org/publishing/docs/wcag/focus-appearance.html
23. Pretendard(동적 서브셋, 가변): https://github.com/orioncactus/pretendard , jsDelivr 버전 목록 https://data.jsdelivr.com/v1/packages/gh/orioncactus/pretendard
