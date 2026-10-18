# UI 테마·CSS 라이브러리 조사 (2026-10-18)

대상: `app/templates/` 5개 화면(base.html 상속, 인라인 CSS 약 40줄). Mac 한 대에서 127.0.0.1로만 여는 1인용 관리 화면이다. 빌드 단계, Node, CSS용 Python 의존성은 두지 않는다.

## 결론

**라이브러리를 쓰지 않는다. base.html의 인라인 `<style>`을 유지하고 70줄 안팎으로 다듬는다.**

- `:root { color-scheme: light dark }` 한 줄로 브라우저가 배경, 글자, input, button, select, 스크롤바의 다크 모드를 처리한다. 직접 칠할 것은 토큰 10개 정도와 배지 색뿐이다.
- 후보 라이브러리 중 상태 배지를 제공하는 것은 없다. 어느 것을 넣어도 배지, `.row`, `.inline`, `tr.off` 같은 CSS는 계속 직접 관리해야 한다. 라이브러리를 넣으면 지금 CSS가 줄지 않고 그 위에 덮어쓰기 CSS만 늘어난다.
- 가장 완성도가 높은 Pico v2도 이 화면과 충돌한다. input과 select가 `width:100%`여서 표 셀 안의 인라인 폼이 줄바꿈되고, 화면이 넓으면 루트 글자 크기를 최대 131%까지 키워 표가 성겨진다.
- CDN도 `app/static`도 쓰지 않는다. 모든 페이지가 base.html을 상속하므로 인라인 `<style>`이 곧 공용 스타일시트다. 파일이 하나뿐인 localhost 앱에서는 StaticFiles mount를 추가해도 캐시 이득이 없다.

## 1. 후보 비교

크기는 jsDelivr에서 받은 파일을 직접 측정했다(`gzip -9`). 버전과 날짜는 npm registry의 latest 기준이다.

| 후보 | 최신 버전 (배포일) | min / gzip | 방식 | 다크 모드 | 표·폼·details·배지 | CJK 폰트 | 좁은 화면의 표 | 유지보수 |
|---|---|---|---|---|---|---|---|---|
| Pico CSS (classless) | 2.1.1 (2025-03) | 71.0 KB / 10.3 KB | classless (`pico.min.css`는 class 기반, 11.7 KB) | 자동 + `data-theme` | 모두 스타일링. 배지 없음(`mark`만). input 100% 폭, 패딩 0.75rem×1rem | `system-ui` 우선이라 Mac에서는 Apple SD Gothic Neo로 대체됨 | `<figure>`로 감싸면 가로 스크롤 | 활발. 2.1.1 이후 태그 없음 |
| Simple.css | 2.3.7 (2025-05) | 9.4 KB / 2.8 KB | classless | 자동 | 스타일링함. 배지 없음 | `-apple-system` 우선 | `table{width:max-content}`, 본문 폭 45rem로 고정 | 보통 |
| Water.css | 2.1.1 (2021-08) | 22.7 KB / 3.6 KB | classless | 자동 + 테마별 빌드 | 스타일링함. 배지 없음 | `system-ui` 우선 | `table-layout:fixed`, 본문 폭 800px | 정체(4년 넘게 릴리스 없음) |
| MVP.css | 1.18.0 (2026-09) | 10.3 KB / 2.7 KB | classless | 자동 | 스타일링함. 랜딩 페이지에 맞춰진 레이아웃 | `-apple-system` 우선 | 별도 처리 없음 | 활발 |
| Milligram | 1.4.1 (2020-06) | 9.0 KB / 2.3 KB | 반(半) class 기반 | **없음** | details 미지원, 배지 없음 | Roboto 고정, 300 weight라 한글이 흐릿함 | 모바일에서 `display:block; overflow-x:auto` | 정체(6년) |
| Bulma | 1.0.4 (2025-04) | 678 KB / 64.9 KB | class 기반 | 지원(1.0부터) | `.tag`가 배지 역할. 마크업 전체를 다시 써야 함 | 시스템 스택 | `.table-container` | 보통 |
| Open Props | 1.7.23 (2026-01) | 29.6 KB / 7.7 KB | 토큰(CSS 변수)만 제공 | 토큰 수준 | 요소 스타일 없음. 규칙은 직접 작성 | 해당 없음 | 해당 없음 | 활발 |
| **직접 작성 (권장)** | — | 약 3 KB / 1 KB 미만, 인라인 | — | `color-scheme` + `light-dark()` | 필요한 것만 작성 | 한글 스택을 명시 | 감싸는 div에 `overflow-x:auto` | 이 repo가 관리 |

라이선스는 모두 MIT다. 버전을 고정한 jsDelivr URL은 불변이므로 SRI(sha384)를 붙일 수 있다(예: Pico classless 2.1.1 → `https://cdn.jsdelivr.net/npm/@picocss/pico@2.1.1/css/pico.classless.min.css`, `sha384-NZhm4G1I7BpEGdjDKnzEfy3d78xvy7ECKUwwnKTYi036z42IyF056PbHfpQLIYgL`). 이 SRI 값은 기록만 해 둔다. 채택하지 않는다.

### 탈락 사유

- **Pico**: 위 두 가지 충돌(input 100% 폭, 글자 크기 확대) 때문에 덮어쓰기가 20줄 이상 필요하다. 그러면 지금 CSS보다 줄이 늘어난다. 10 KB gzip도 화면 5개에 비해 크다.
- **Simple.css / Water.css / MVP.css**: 블로그나 문서용이다. 본문 폭 45rem 또는 800px, 큰 글자를 전제한다. 표가 많은 관리 화면에서는 폭을 풀어야 한다. Water는 정체 상태다.
- **Milligram**: 다크 모드가 없고 Roboto 300 weight에서 한글이 흐릿하다. 정체 상태다.
- **Bulma**: 65 KB gzip이고 class를 템플릿 전체에 붙여야 한다. "가장 게으른 방법" 원칙에 정반대다.
- **Open Props**: 토큰만 주므로 규칙은 결국 직접 쓴다. 이 앱의 토큰은 10개 정도라 손으로 써도 된다.

## 2. 소규모 운영·관리 화면의 관례

| 주제 | 관례 | 이 repo 적용 |
|---|---|---|
| 상태 색 | Healthchecks.io 배지: up 초록, late 주황, down 빨강. Uptime Kuma: 정상 초록, 재시도 대기 노랑, 다운 빨강, 점검 파랑 | 현행 매핑(ok/done 초록, partial/domain_moved 호박색, 오류 계열 빨강, running 파랑)이 관례와 같다. 그대로 둔다. 색만으로 구분하지 않도록 텍스트 라벨도 유지한다(이미 그렇게 되어 있음) |
| 다음 실행 / 마지막 실행 | Healthchecks는 "last ping"과 예상되는 다음 시각을 나란히 보여준다 | 이미 절대시각을 표시한다. "N분 후"는 렌더 시점에 고정되어 곧 틀린 값이 된다. 넣는다면 서버에서 `(약 N분 후)`로 한 번 계산해 덧붙이는 정도로 충분하다. JS 카운트다운은 넣지 않는다 |
| 삭제 확인 | htmx는 `hx-confirm`(내부적으로 `window.confirm`)을 쓴다. JS가 없을 때의 대안은 별도 확인 페이지다 | 삭제 폼 하나에 `onsubmit="return confirm('삭제할까요?')"`를 붙인다. htmx나 확인 페이지는 쓰지 않는다 |
| 인라인 편집 vs 별도 페이지 | 필드가 2–3개면 인라인, 많으면 별도 페이지 | 사이트 편집은 url+boards 두 필드라 `<details>` 인라인이 맞다. 그대로 둔다 |
| 빈 상태 | 표 안에 한 줄로 "아직 없음"을 표시하고, 가능하면 다음 행동을 안내한다 | index.html은 이미 그렇게 한다. programs 표에도 `{% else %}`로 "위에서 프로그램을 추가하세요" 한 줄을 넣는다 |
| 좁은 화면의 표 | 비교가 필요한 조밀한 데이터는 가로 스크롤을 쓴다. 카드형으로 쌓는 방식은 짧은 표에만 맞고 표 의미론을 잃을 위험이 있다 | 표를 `overflow-x:auto` div로 감싼다. 카드형은 만들지 않는다. 다만 사용 환경이 Mac 데스크톱뿐이라 우선순위는 낮다 |
| 다크 모드 | 셀프호스팅 도구(Uptime Kuma, Healthchecks dashboard 등)는 다크 테마를 기본 제공하거나 토글한다 | OS 설정을 따른다(`color-scheme: light dark`). 토글 버튼과 설정 저장은 만들지 않는다 |

## 3. 통합 스케치

바꿀 파일은 `app/templates/base.html` 하나다. `main.py`, Dockerfile, 의존성은 그대로 둔다.

```css
:root {
  color-scheme: light dark;              /* 배경·글자·폼 컨트롤 다크 모드를 브라우저가 처리 */
  --fg: light-dark(#222, #ddd);  --muted: light-dark(#777, #999);
  --line: light-dark(#ddd, #3a3a3a);  --soft: light-dark(#f6f6f6, #1e1e1e);
  --link: light-dark(#0b5cad, #6ea8fe);
  --ok: light-dark(#1e7b34, #6fcf87);   --ok-bg: light-dark(#e3f4e5, #12301a);
  --warn: light-dark(#8a5a00, #f0c060); --warn-bg: light-dark(#fdf1d8, #3a2c0a);
  --bad: light-dark(#a12622, #f28b82);  --bad-bg: light-dark(#fdecea, #3b1513);
  --run: light-dark(#1d5bb8, #8ab4f8);  --run-bg: light-dark(#e3edfb, #152a4a);
}
body { font-family: system-ui, -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", "Noto Sans KR", sans-serif;
       color: var(--fg); background: Canvas; word-break: keep-all; /* 한글을 어절 단위로 줄바꿈 */ }
/* 현행 규칙의 #ddd/#f5f5f5/#888 등을 var(--line)/var(--soft)/var(--muted)로 치환 */
.badge.ok, .badge.done { background: var(--ok-bg); color: var(--ok); }   /* 나머지 배지도 같은 방식 */
.scroll { overflow-x: auto; }   /* <div class="scroll"><table>…</table></div> */
```

- `light-dark()`는 Chrome 123, Safari 17.5, Firefox 120부터 지원한다(Baseline 2024). 단일 사용자 Mac의 최신 브라우저에서는 문제가 없다. 구형 브라우저를 지원해야 하면 `@media (prefers-color-scheme: dark) { :root { … } }`로 같은 변수를 다시 정의하면 된다. 줄 수는 거의 같다.
- 결과적으로 이 프로젝트가 관리하는 CSS는 약 **70줄**(현행 40줄 + 토큰 15줄 + 소소한 추가)이다. 외부 파일과 요청은 0개다.
- 나중에 CSS가 150줄을 넘으면 그때 `app/static/app.css`로 분리하고 `app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")`를 추가한다. StaticFiles는 FastAPI(Starlette)에 내장되어 있어 의존성이 늘지 않는다. 지금은 하지 않는다.

## 4. 의도적으로 하지 않는 것

- CSS 프레임워크, CDN 스타일시트, 웹폰트(Pretendard 등): 시스템 폰트(Mac은 Apple SD Gothic Neo)로 충분하다.
- 다크/라이트 토글 버튼과 설정 저장: OS 설정을 따른다.
- 표를 카드형으로 쌓는 모바일 레이아웃: 화면을 Mac 데스크톱에서만 연다.
- JS로 "N분 후" 카운트다운, 토스트, 모달 확인창: `window.confirm`과 서버 렌더 문구로 충분하다.
- 아이콘 세트, 사이드바, 그리드 시스템.

## 출처

- Pico CSS: https://picocss.com/docs , https://github.com/picocss/pico , https://packagist.org/packages/picocss/pico
- Simple.css: https://github.com/kevquirk/simple.css
- Water.css: https://github.com/kognise/water.css
- MVP.css: https://github.com/andybrewer/mvp
- Milligram: https://github.com/milligram/milligram
- Bulma: https://bulma.io
- Open Props: https://open-props.style
- 크기, 버전, SRI: https://registry.npmjs.org/ , https://cdn.jsdelivr.net/npm/ (2026-10-18 직접 측정)
- 분류 비교: https://best-of-web.builder.io/library/kognise/water.css , https://best-of-web.builder.io/library/andybrewer/mvp
- Healthchecks 상태 색: https://healthchecks.sre.cfainstitute.org/docs/badges/ , https://github.com/healthchecks/dashboard
- Uptime Kuma 상태 색(커뮤니티 설명): https://scratch.mit.edu/discuss/topic/692358 , https://deepwiki.com/Alice39s/kuma-mieru/7.4-status-and-color-systems
- 삭제 확인: https://v1.htmx.org/attributes/hx-confirm , https://thevalleyofcode.com/htmx/9-confirm-and-prompts
- 반응형 표: https://tools.simonwillison.net/mobile-tables , https://gomakethings.com/responsive-tables
- `light-dark()` / `color-scheme`: https://developer.mozilla.org/docs/Web/CSS/color_value/light-dark , https://web.dev/articles/light-dark , https://developer.mozilla.org/en/docs/Web/CSS/color-scheme
- 한글 폰트 스택: https://github.com/orioncactus/pretendard , https://dev.to/agw76638/building-sleek-korean-web-pages-using-only-system-fonts-no-web-fonts-4ln6 , https://chromium.googlesource.com/chromium/src.git/+/b964e3614ed0e915a2c46a09d46c32152919b8a9
