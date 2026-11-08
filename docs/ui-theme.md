# UI 테마: TTY

웹 UI 전체를 80칸 터미널 텍스트 모드로 그린다. 원안은 다른 제품(agent-pod)용 "6 · TTY" 시안이다. 그 시안의 시각 언어(요소와 규칙)만 가져와 우리 화면에 대응시킨다. 화면 구성과 문구는 우리 것을 유지한다.

원칙(시안 원문 요약):
- 모노스페이스 격자 하나, 글자 크기 하나. 위계는 밝기, 굵기, 반전(inverse video)으로만 만든다.
- 이중선 상자 위 테두리에 제목을 건다(`╡ 제목 ╞`). 선택 항목은 반전한다. 단축키는 바닥 줄에 둔다.
- 상태는 기호만으로 읽힌다: `[ok]` `[!!]` `[>>]` `[??]`. 색은 ANSI-256 네 가지(노랑, 빨강, 청록, 초록)뿐이다.
- 참고: VT220, Midnight Commander, htop, tig/lazygit, IBM 3270.

빌드 도구, 새 의존성, CSS 프레임워크는 쓰지 않는다. 파일은 `app/static/app.css` 하나, `app/templates/*.html`, `app/templates/_macros.html`이다.

## 1. 전략

### 1.1 층

`app.css` 한 파일을 아래 순서의 주석 구획으로 나눈다. 뒤 구획이 앞 구획을 덮는다. `@layer`는 쓰지 않는다. 파일이 400줄 안팎이라 순서만으로 충분하다.

| 구획 | 담는 것 | 규칙 |
|---|---|---|
| tokens | `:root` 사용자 정의 속성 | 색, 글꼴, 줄 높이, 테두리 값은 여기에만 쓴다. 다른 구획에 hex 값을 쓰지 않는다 |
| base | 요소 선택자(`body`, `a`, `h1`, `button`, `input`, `:focus-visible`, `kbd`, `pre`) | 클래스 없이 읽혀도 TTY로 보이게 한다 |
| shell | 제목 줄, 본문 두 단(`.row`, `.side`, `.main`), dev 줄, 바닥 키 줄 | `base.html`에만 나오는 것 |
| components | 2장의 컴포넌트 | 클래스 이름은 역할로 짓는다. 화면 이름을 넣지 않는다 |
| pages | 한 화면에만 쓰는 배치(`.stats`, `.sites`) | 최소한으로 둔다. 같은 모양이 두 화면에 나오면 components로 올린다 |
| utilities | `.hi` `.dim` `.y` `.r` `.c` `.g` `.sr-only` | 맨 끝에 둔다 |

다크 한 벌만 둔다. `color-scheme: dark`이고 `prefers-color-scheme` 분기는 없다.

### 1.2 토큰

색(시안 값 그대로):

| 토큰 | 값 | 용도 |
|---|---|---|
| `--bg` | `#000000` | 바탕 |
| `--fg` | `#C8C8C8` | 본문 글자, 반전 바탕(`--inv`와 같은 값) |
| `--hi` | `#FFFFFF` | 강조 글자, 제목, 값 |
| `--dim` | `#8A8A8A` | 라벨, 보조 글자, 단축키 열 |
| `--raise` | `#262626` | 입력칸 바탕, 현재 행 바탕 |
| `--line` | `#4A4A4A` | 1px 구분선(표 머리, 그룹, 키 줄) |
| `--frame` | `#6E6E6E` | 상자 이중선 |
| `--inv` | `#C8C8C8` | 반전 바탕(선택 항목, 제목 줄, 주 버튼, 키 캡). 반전 글자는 `--bg` |
| `--y` | `#FFD75F` | `[??]` 사람이 볼 것, 주의 버튼, 개수 |
| `--r` | `#FF5F5F` | `[!!]` 실패, 실패 상자 테두리 |
| `--c` | `#5FD7FF` | `[>>]` 실행 중 |
| `--g` | `#87D787` | `[ok]` 정상, 양수 |

`--raise` 위에서는 `--dim`을 `#949494`로 다시 선언한다(`.cur, .in { --dim: #949494 }`). 이유는 4장.

글꼴과 격자:

| 토큰 | 값 |
|---|---|
| `--font` | `'Nanum Gothic Coding', 'D2Coding', ui-monospace, monospace` |
| `--font-big` | `VT323, monospace` |
| `--fs` / `--lh` | `14px` / `22px`. 모든 글자가 이 한 크기다. `h1`~`h3`, `small`, `strong`도 크기를 바꾸지 않는다 |
| 큰 글자 | `var(--font-big)` `44px/44px` (두 줄 높이). 큰 숫자와 상세 화면 번호(`#12`, `404`)에만 쓴다. VT323에는 한글이 없으므로 한글 제목에는 쓰지 않는다 |
| 로고 | `var(--font-big)` `20px/22px`, `letter-spacing: .06em`. 시안은 24px 줄이지만 제목 줄을 22px 격자에 맞춘다 |

`body`에 `word-break: keep-all`을 둔다. 나눔고딕코딩은 한글 한 자를 두 칸 폭으로 그린다.

간격:
- 가로 간격은 `ch` 단위만 쓴다. 칸 사이 `1ch`, 묶음 사이 `2ch`, 라벨 열 `8ch`(폼) 또는 `10ch`(키-값).
- 세로 리듬은 줄 높이 22px이다. 컨트롤, 표 행, 메뉴 항목의 높이는 모두 22px이다.
- 시안의 세로 값을 그대로 쓴다: 본문 여백 `24px 2ch 28px`, 두 단 사이 `24px 2ch`, 상자 사이 `30px`(상자 제목이 위 테두리에 13px 걸치는 몫을 흡수한다), 상자 안쪽 `16px 2ch 12px`.

테두리:
- 상자: `3px double var(--frame)`. 실패 상자 `.box.bad`는 `--r`, 경고 상자 `.box.warn`은 `--y`.
- 구분선: `1px solid var(--line)`.
- 둥근 모서리, 그림자, 그라디언트 배경, 아이콘은 없다. 막대(`.bar`)만 `repeating-linear-gradient`로 칸을 그린다.

### 1.3 글꼴 불러오기

`base.html`의 Pretendard 링크를 지우고 Google Fonts 하나로 바꾼다.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nanum+Gothic+Coding:wght@400;700&family=VT323&display=swap">
```

글꼴이 늦거나 막히면 `D2Coding`, 시스템 모노스페이스로 그린다. 격자는 `ch`와 `px`로 정했으므로 대체 글꼴에서도 무너지지 않는다.

`CSS_V`(cache-buster)는 `views.py` import 시점의 `app.css` mtime이다. uvicorn `--reload`는 `*.py`만 보므로 CSS만 고친 뒤에는 `app/views.py`를 `touch`해야 새 `?v=`가 붙는다.

## 2. 컴포넌트

"매크로" 열이 예인 것만 `_macros.html`에 둔다. 나머지는 마크업이 한두 줄이라 그대로 쓴다.

| 컴포넌트 | 클래스 | 마크업 | 매크로 |
|---|---|---|---|
| 제목 줄 | `.title`, `.logo`, `.title .rt` | `<header class="title"><a class="logo" href="/">TORRENT</a><span>─ {% block crumb %}</span><span class="rt">…</span></header>` 반전 바탕, 한 줄, 줄바꿈 허용 | 아니오(`base.html`) |
| 이중선 상자 | `.box`, `.bt`, `.box.bad`, `.box.warn`, `.box.off` | `<section class="box"><h2 class="bt">제목</h2>…</section>`. `╡ ` `╞`는 `.bt::before/::after`의 CSS `content`로 그리고 대체 텍스트를 비운다(`content: "╡ " / ""`). `.bt`는 `max-width: calc(100% - 6ch)`, 넘치면 말줄임 | 예: `box(title, tone=none, el="section")` + `caller()` |
| 메뉴 목록 | `.side`(상자), `.it`, `.it .k`, `.it .n`, `.it .cn`, `.sep` | `<a class="it" href="/sites" aria-current="page" data-g="s"><span class="k">g s</span><span class="n">사이트</span><span class="cn">1</span></a>`. 선택 표시는 `.on` 클래스가 아니라 `[aria-current="page"]` 선택자로 반전한다 | 아니오(`base.html` 루프) |
| 탭 | `.tabs`, `.tab` | 쓰는 화면이 없다. CSS도 두지 않는다 | - |
| 대괄호 버튼 | `.btn`, `.btn.rev`(주), `.btn.ya`(주의), `.btn.r`(삭제) | `<button class="btn rev">지금 실행</button>`. `[ ` `]`는 `::before/::after`, 대체 텍스트는 비운다. `.rev`/`.ya`만 바탕색이 있고 `padding: 0 .5ch`. `:disabled`는 `--dim`, `cursor: not-allowed`. `<a class="btn">`도 같은 모양 | 아니오 |
| 켜기 스위치 | `.chk` | `<button class="chk" role="switch" aria-checked="true" aria-label="토렌트썸 사용">사용</button>`. `::before`가 `aria-checked`에 따라 `[x] ` / `[ ] `를 그린다. 켜짐은 `--hi`, 꺼짐은 `--dim`. 지금처럼 hidden input과 함께 form POST 한다 | 아니오 |
| 체크박스 | `.ck` | `<label class="ck"><input type="checkbox" …><span>720p</span></label>`. input은 시각적으로 숨기고(`opacity:0; position:absolute`) `span::before`가 `[ ] `/`[x] `를 그린다. `input:focus-visible + span`에 포커스 테두리 | 아니오 |
| 폼 줄 | `.form`, `.fl`, `.lb` | `<div class="fl"><label class="lb" for="x">이름</label><input class="in" id="x"></div>`. `.fl`은 flex-wrap, `.lb`는 `8ch` `--dim` | 아니오 |
| 입력칸 | `.in`(input, select, textarea 공통) | 바탕 `--raise`, 글자 `--hi`, 테두리 없음, 모서리 0, `padding: 0 1ch`, 높이 22px(textarea는 22px의 배수). `box-shadow: inset 0 -1px var(--dim)`로 밑줄을 그린다. select는 `appearance: none` 뒤에 `::after`가 없으므로 값 뒤에 ` ▾`를 넣지 않고 밑줄로만 구분한다. placeholder는 `--dim` | 아니오 |
| 표 | `.tw`(스크롤 틀), `table.grid`, `.grid th`, `.grid .num`, `.grid .end`, `tr.cur`, `tr.off` | `<div class="tw"><table class="grid">…</table></div>`. 진짜 `<table>`을 쓴다(시안의 div 격자 대신). `th`는 `--dim`, 아래 `1px --line`. 칸 `padding: 0 1ch`, 행 22px, 세로선과 행 구분선 없음. `tr.cur`와 `tbody tr:hover`, `tbody tr:focus-within`은 `--raise` 바탕. `white-space: nowrap`이고 긴 칸은 `.cut`(`max-width: 40ch`, 말줄임, `title` 속성) | 아니오 |
| 그룹 구분 | `.grp`(표 안), `.sep`(메뉴 안) | 표: `<tr class="grp"><th colspan="5" scope="colgroup"><span>11-08 · 3</span></th></tr>`, 글자 뒤로 `1px --line`이 칸 끝까지 이어진다. 표 칸은 flex가 될 수 없어(`colspan`이 풀린다) `th` 바탕 그라디언트로 선을 긋고 검정 바탕 `span`이 글자 자리를 가린다. 메뉴: `<div class="sep">외부</div>` | 아니오 |
| 상태 태그 | `.tag` + 색 클래스 | `<span class="tag g" title="ok"><span aria-hidden="true">[ok]</span> 정상</span>`. 기호는 스크린리더에서 숨기고 한국어 라벨을 항상 함께 보인다. 아래 표로 매핑 | 예: `tag(s, text=none, tone=none)`(지금 `badge` 대체) |
| 알림 줄 | `.msg` | `<div class="msg" role="status">{{ tag 기호 }} 설정을 바꿨습니다. <form …><button class="btn">지금 실행</button></form></div>`. 안에 `form`이 들어갈 수 있어 `p`가 아니라 `div`다. 상자 없이 한 줄, 기호 색만 다르다 | 예: `flash(error, msg, n)`(시그니처 유지) |
| 빈 상태 | `.empty` | `<p class="empty dim">아직 실행 기록이 없습니다. 지금 실행을 누르거나 다음 실행을 기다리세요.</p>` 한 문단, 가운데 정렬 안 함 | 예: `empty(title, hint)` |
| 키-값 목록 | `dl.kv` | `<dl class="kv"><div><dt>최근 성공</dt><dd>…</dd></div>…</dl>`. 각 `div`가 `grid-template-columns: 10ch minmax(0,1fr)`, `dt`는 `--dim`, `dd`는 `--hi`, `overflow-wrap: anywhere`. `dd` 안 보조 글자는 `.dim` | 아니오 |
| 로그 | `pre.log`, `mark.log-bad`, `.cmd` | `<pre class="log">`. 바탕, 테두리 없음, 글꼴과 크기는 본문과 같다, `white-space: pre-wrap`, `max-height: 60vh; overflow: auto`. `mark.log-bad`는 바탕 없이 `--r` 글자. 클래스 이름 `log`, `log-bad`, `id="progress"`는 `doctor.py`와 테스트가 쓰므로 바꾸지 않는다. `.cmd`(`$ 명령` 줄)는 보여줄 실제 명령이 없어 쓰지 않는다 | 아니오 |
| 목록 | `ul.list` | `li::before { content: "* " / ""; color: var(--dim) }` | 아니오 |
| 막대 | `.bar` + 색 클래스 | `<span class="bar g" style="--n: 8"></span>` 폭 `calc(var(--n) * 1ch)`, 높이 12px, 칸 사이 2px 틈. 색만으로 읽히지 않게 옆에 숫자를 함께 쓴다 | 아니오 |
| 큰 숫자 | `.big` | `<span class="big">8/10</span>` `--font-big` 44px/44px `--hi` | 아니오 |
| 화면 머리 | `.hd`, `.hd h1`, `.hd .rt` | `<div class="hd"><h1>대시보드</h1><span>10분마다 확인</span><span class="dim">·</span><span>…</span><span class="rt"><form …><button class="btn rev">지금 실행</button></form></span></div>`. `h1`은 `700 --hi` 14px. 상세 화면 번호만 `h1.big` | 아니오 |
| 접기 | `details.fold`, `details.edit` | `summary`가 버튼 모양. `.edit > summary`는 `[ 수정 ]` ↔ `[ 닫기 ]`(지금 `.editor` 방식 그대로 `::after` content 교체), `.fold > summary`는 앞에 `[+] `/`[-] ` | 아니오 |
| 바닥 키 줄 | `.keys`, `.keys kbd`, `.keys .rt` | `<footer class="keys"><span><kbd>g d</kbd>대시보드</span>…<span class="rt">상태 줄</span></footer>`. `kbd`는 반전, `padding: 0 .5ch` | 아니오(`base.html`) |
| 글자 유틸 | `.hi` `.dim` `.y` `.r` `.c` `.g` `.sr-only` | 색만 바꾼다 | - |

상태 태그 매핑. 지금 CSS의 배지 색 분류(ok/warn/bad/running/중립)를 그대로 옮긴다. 상태 키 → 색 묶음은 `views.py`의 `TONE` dict 한 곳에 둔다(`LABEL` 옆). `tag` 매크로가 `TONE.get(s, "none")`으로 기호와 색을 고른다.

| 묶음 | 기호 | 색 | 우리 상태 키 | 뜻 |
|---|---|---|---|---|
| `ok` | `[ok]` | `.g` | `ok`, `done` | 정상, 완료 |
| `bad` | `[!!]` | `.r` | `error`, `blocked`, `site_down`, `cloudflare`, `parser_broken` | 실패 |
| `run` | `[>>]` | `.c` | `running` | 실행 중, 진단 중 |
| `warn` | `[??]` | `.y` | `partial`, `domain_moved`, `transient`, 사이트 응답 없음(stale) | 사람이 확인할 것 |
| `none` | `[--]` | `.dim` | `auto_changed`, `domain_probe`, `redirect`, 기록 없음, 재시작 중단, 그 밖의 키 | 정보 |

`[--]`는 시안에 없는 다섯째 기호다. 색이 없는 중립 상태를 기호로 읽게 하려고 둔다.

## 3. 화면 대응

### 3.1 `base.html` (셸)

| 지금 | 바뀐 뒤 |
|---|---|
| Pretendard `<link>` | 1.3의 Google Fonts `<link>` |
| `<title>[dev] …</title>` | 그대로 |
| `.topbar` + `.brand` "torrent" | `header.title`: `.logo` "TORRENT"(VT323, `/` 링크) · `─ {% block crumb %}{{ self.title() }}{% endblock %}` · `.rt`에 Transmission 호스트(`TM_HOST`), dev 표시, 렌더 시각(`now|dt`) |
| `.badge.env` "DEV" | `.title .rt` 안 `<span class="env">DEV</span>`: 노랑 바탕 검정 글자(반전 위 반전) |
| `.envbar` dry-run 안내 | 제목 줄 바로 아래 한 줄 `<p class="envline y">[dev] dry-run — …</p>`, 아래 `1px --line`. 문구는 그대로 |
| `nav.nav` 가로 링크 | `.row` 왼쪽 `nav.box.side`(`aria-label="주 메뉴"`, 제목 `이동`은 `h2`가 아니라 `<span class="bt" aria-hidden="true">`. 이름은 `aria-label`이 준다): `.it` 셋(`g d` 대시보드, `g p` 프로그램, `g s` 사이트 + 응답 없는 사이트 수 `.cn`), `.sep` "외부", `.it` Transmission(`.k`에 `↗`, 새 탭). `cur` 계산과 `aria-current`는 지금 로직 그대로 |
| `main.main.wrap` | `main.main`(`.row` 오른쪽 단, 자식 사이 `30px`) |
| 없음 | `footer.keys`: `g d` `g p` `g s` 키 캡, `.rt`에 상태 줄(`[>>] 실행 중` 또는 `다음 실행 11:20`, 응답 없는 사이트가 있으면 `.y` `사이트 경고 1`) |
| 없음 | `<head>` 안 인라인 단축키 스크립트(5장 1번) |

### 3.2 대시보드 `index.html`

| 지금 | 바뀐 뒤 |
|---|---|
| `meta refresh`(10초/60초) | 그대로 |
| `.page-head` h1 + `.sub` | `.hd`: `h1` 대시보드 · `N분마다 자동으로 확인합니다` · `Transmission host(user)`. `.rt`에 `[ 지금 실행 ]` `.btn.rev`(▶ 아이콘 삭제) |
| `flash(msg)` | `flash` 매크로 새 마크업(`.msg`). `applied`의 `[ 지금 실행 ]`은 `.btn` |
| `.card.hero.is-*` | `box("상태", tone)`: `is-bad` → `.box.bad`, `is-warn` → `.box.warn`. 첫 줄 `tag` + 제목 `.hi` 굵게(예: `[ok] 정상`, `[??] 정상 · 사이트 2곳 응답 없음`). 깜빡이는 점과 `@keyframes blink` 삭제 |
| `.hero-meta` 줄들 | 같은 상자 안 `dl.kv`: `마지막` `#12 · 11-08 09:20 · 3분 전`, `결과` `매칭 4 · 추가 1 · 2분 3초 · 로그 보기`, `다음` `11-08 10:20 · 57분 후`(실행 중이면 `[>>] 실행 중`) |
| `.hero-side` 다음 실행 | 위 kv `다음` 행으로 합친다 |
| `.hero-foot` 주기 폼 | 같은 상자 맨 아래 `.fl`: `.lb` 주기 · `input.in[type=number]` `6ch` · `분` · `[ 저장 ]` |
| `dl.stats` 타일 4개 | `box("요약")` 안 `.stats` 격자(`repeat(auto-fit, minmax(18ch, 1fr))`): 각 칸 `dt` `--dim`, 값 `.big`(경고 `.y`, 실패 `.r`), 힌트 `.dim`. `최근 실행` 칸은 값 아래 `.bar.g`(정상 수) + `.bar.r`(실패 수). 사이트/프로그램 칸의 `dt` 링크와 칸 전체 클릭 영역은 유지 |
| 최근 실행 `.card` + `.table` | `box("최근 실행 · 10")` + `.tw > table.grid`: `#`(`.hi` 링크) · 시작 · 소요 · 상태(`tag`) · 매칭 · 추가(`> 0`이면 `.g`). 실행 중 행은 `tr.cur`. `.hide-sm` 삭제(`.tw`가 가로 스크롤) |
| 다운로드 `.card` + `.table` | `box("다운로드 · 20")` + `table.grid`. 날짜가 바뀔 때마다 `tr.grp`(`loop.changed(d.added_at[:10])`, 템플릿만으로). 제목 칸 `.cut`. `.show-sm` 중복 제목 삭제 |
| `.empty` 두 개 | `empty()` 매크로, 문구 그대로 |

### 3.3 프로그램 `programs.html`

| 지금 | 바뀐 뒤 |
|---|---|
| `.page-head` | `.hd`: `h1` 프로그램 · `켜짐 n · 전체 m` · `.dim` `위에 있을수록 먼저 매칭됩니다` |
| `flash(error, msg)` | `.msg`, 오류는 `[!!]` `.r` |
| 새 프로그램 `.card` 폼 | `box("새 프로그램", el="form")`: `.fl` 이름(`input.in`, `flex: 1 1 30ch`) · `fieldset` 해상도(`legend.lb`, `.ck` 셋) · `[ + 추가 ]` `.btn.rev`. `.hint` → `.dim` 문단 |
| 목록 `.card` + `.table` | `box("목록 · m")` + `table.grid`: 순서(`.dim .num`) · 이름(켜짐 `.hi`, 꺼짐 행 `tr.off` 전체 `--dim`이되 `[ 삭제 ]`는 붉게, `<strong>` 삭제) · 해상도 · 켜기 · 삭제 |
| 해상도 `details.res-edit` + `.btn-ghost` summary ▾ | `details.edit`의 summary를 `.btn`(`[ 720p · 1080p ]`, sr-only `, 이름 해상도 수정` 유지). 펼치면 `.ck` + `[ 저장 ]` |
| `.switch` 토글 | `.chk`(`[x] 사용` / `[ ] 사용`), `aria-label` 유지 |
| `.btn-danger` 삭제 + `confirm()` | `.btn.r` `[ 삭제 ]`, `onsubmit confirm()` 그대로 |
| `.empty` | `empty()` |

### 3.4 사이트 `sites.html`

| 지금 | 바뀐 뒤 |
|---|---|
| `.page-head` + 진단 모델 폼 | `.hd`: `h1` 사이트 · `켜진 n곳` · `.dim` `최근 성공이 N분 넘게 없으면 경고합니다`. `.rt`에 `.lb` 진단 모델 · `select.in` · `[ 저장 ]` |
| `flash` | `.msg` |
| `.site-grid` | `.sites`: `grid-template-columns: repeat(auto-fill, minmax(min(100%, 60ch), 1fr))`, 간격 `30px 2ch` |
| `.card.site`, `.is-warn`, `.off` | `box(s.name)`: 응답 없음 → `.box.warn`, 꺼짐 → `.box.off`(글자 전부 `--dim`, 투명도 아님). `aria-labelledby` 대신 `h2.bt` |
| `.site-id` h2 + URL 링크 + `auto_changed` 배지 | `dl.kv` 첫 행 `URL`: 링크 `torrentsome268.com ↗`(sr-only `(새 탭)` 유지), 최근 7일 안 자동 변경이면 뒤에 `tag("auto_changed")` |
| `.site-facts` 최근 성공 / 최근 진단 | 같은 `dl.kv`의 `최근 성공`(`tag` warn `응답 없음` + 시각 + `.dim` 상대 시각), `최근 진단`(`tag(verdict)` + 링크, 진단 중이면 `tag("running", "진단 중")`) 행 |
| `details.url-changes` | `dl.kv` `변경 이력` 행 안 `details.fold`: summary `URL 자동 변경 8건`, 펼치면 `ul.list` 줄 `11-08 09:00 · x6.com → x7.com · 리다이렉트`. 두 문구 형식은 테스트가 고정하므로 바꾸지 않는다 |
| `.site-ctrl` 스위치 + 진단 버튼 | 상자 맨 아래 `.acts` 한 줄(`1ch` 간격): `.chk` 사용 · `[ 진단 · 최대 $1 ]`(응답 없음이면 `.btn.ya`, 진단 중이면 `disabled`) · 수정 |
| `details.editor` | `details.edit` summary `[ 수정 ]`/`[ 닫기 ]`. 본문 `.form`: `.fl` URL(`input.in[type=url]`) · 게시판(`textarea.in`, `.lb` 아래 `.dim` `한 줄에 하나`) · 페이지(`input.in[type=number]`, 뒤에 `.dim` `게시판마다 1~N쪽`. `페이지 수`는 `.lb` 8ch를 넘어 줄이 바뀌므로 줄였다) · `[ 저장 ]` `.btn.rev` |

### 3.5 실행 상세 `run.html`

| 지금 | 바뀐 뒤 |
|---|---|
| `.back` `← 대시보드` | 삭제. `{% block crumb %}<a href="/">대시보드</a> / 실행 #12{% endblock %}` |
| `h1.title-row` + 배지 + `.sub` | `.hd`: `h1.big` `#12` · `tag(run.status)` · 시작 · 소요 · `매칭 n · 추가 n`(`.dim` `·` 구분) |
| `.flash-info` 재시작 중단 | `.msg` `[--]` 문구 그대로 |
| `.flash-bad` + 사이트 확인 링크 | `.msg` `[!!]` `.r` + 링크 `사이트 확인` |
| 로그 `.card` | `box("로그 · 1,234줄")` + `pre.log` |
| `.empty` | `empty()` |

### 3.6 진단 `doctor.html`

| 지금 | 바뀐 뒤 |
|---|---|
| htmx `<script>`(진행 중일 때만) | 그대로 |
| `.back` `← 사이트` | crumb `<a href="/sites">사이트</a> / 진단 · 토렌트썸` |
| `.page-head` | `.hd`: `h1` `진단 · 이름`(굵게, 14px) · 모델 · 시작 시각(상대) · 비용 또는 `진행 중 · 상한 $1` |
| `.card.hero.is-*` | `box("결과", tone)`: 첫 줄 `tag` + 제목(`[>>] 진단 중입니다 · 상한 $1`, `[ok] 정상`, `[!!] 진단을 끝내지 못했습니다`), 다음 줄 요약 `.hi`. `max-width: 96ch`는 `box`의 키워드 인자 `style=`로 준다(`box`는 나머지 키워드를 `xmlattr`로 붙인다) |
| 수정 제안 `.card` + `table.diff` | `box("수정 제안")` + `dl.kv`: `URL` 행 dd 안 두 줄 `<span class="r">- </span>현재값` / `<span class="g">+ </span>제안값`(각 줄 앞 sr-only `현재: `/`제안: `), 같으면 현재값 뒤 `.dim` `같음`. 게시판도 같은 방식으로 값마다 한 줄(`<br>`)이고 줄마다 `- `/`+ `가 붙는다. 템플릿 안 `diff(old, new)` 매크로 하나가 두 행을 그린다. `table.diff`와 모바일 `data-label` CSS 삭제 |
| `.card-foot` 적용 버튼 + `confirm()` | 같은 상자 아래 `[ 이 설정으로 변경 ]` `.btn.rev`, `confirm()` 그대로 |
| 현재 설정 `.card` | `box("현재 설정")` + `dl.kv`, 제목 뒤 `.dim` `수정 제안 없음`은 상자 첫 줄로 |
| 근거 `.card` + `ul.list` | `box("근거")` + `ul.list` |
| 진행 로그(진행 중) `pre#progress.log` + `hx-*` | `box("진행 로그 · 2초마다 새로 고침")` + 같은 `pre`, `hx-*` 속성과 `doctor.py`의 조각 응답은 그대로 |
| 진행 로그(끝남) `details.card.fold` | `details.box.fold`, summary가 `.bt`(`[+] 진행 로그 · n줄`). `.bt::before`와 `.fold` 표시가 같은 가상 요소를 쓰므로 `summary.bt::before`가 `╡ [+] `/`╡ [-] `를 함께 그린다. 결과가 없으면 `open` 유지 |

### 3.7 오류 `error.html`

| 지금 | 바뀐 뒤 |
|---|---|
| `.card.error-card` 가운데 정렬 | `box("오류", tone="bad", style="max-width: 60ch")`, 왼쪽 정렬 |
| `.error-code` | `.big.r` `404` |
| `.error-msg` | `.hi` 문단 |
| `[대시보드로]` primary, `[뒤로]` ghost | `[ 대시보드로 ]` `.btn.rev`, `[ 뒤로 ]` `.btn`(referer 조건 그대로) |
| 메뉴 `cur` 없음 | 그대로(`code is defined`면 `aria-current` 없음) |

### 3.8 JS로 움직이는 것 (지금 있는 것)

- `index.html` `meta refresh`: 유지.
- `doctor.html` htmx 2초 폴링, 끝나면 `HX-Refresh`: 유지. `pre#progress.log` 마크업이 `doctor.py`에 하드코딩돼 있으므로 클래스를 바꾸지 않는다.
- `programs.html` 삭제, `doctor.html` 적용의 `onsubmit confirm()`: 유지.
- `details/summary` 접기: JS 없음, 유지.
- 새로 더하는 것은 단축키 스크립트 하나다(5장).

## 4. 반응형과 접근성

### 4.1 반응형

폭 breakpoint는 두지 않는다. flex-wrap과 `auto-fill`만으로 쌓인다.
- `.row`: `.side`(`flex: 1 1 232px`)와 `.main`(`flex: 999 1 560px`)이 들어갈 폭이 안 되면 메뉴 상자가 위로, 본문이 아래로 쌓인다.
- `.title`, `.hd`, `.fl`, `.acts`, `.keys`는 `flex-wrap: wrap`.
- 표는 늘 `.tw`(`overflow-x: auto`) 안에 둔다. 표가 좁아지지 않고 틀 안에서 가로로 스크롤한다. `.hide-sm`, `.show-sm`은 없앤다.
- 사이트 상자는 `minmax(min(100%, 60ch), 1fr)`로 폰 폭에서 한 줄에 하나.
- `.bt`는 상자 폭보다 길면 말줄임.
- 터치 기기(`@media (pointer: coarse)`): `.btn`, `.chk`, `.ck`, `.it`, `summary`의 `line-height`를 `44px`(두 줄)로 키운다. 격자 배수라 리듬이 유지되고 터치 영역 24px 이상(WCAG 2.5.8)을 지킨다.
- 마우스 없는 기기(`@media (hover: none)`): 키 줄의 `kbd` 항목과 메뉴의 `.k` 열을 숨긴다. 키 줄 오른쪽 상태 줄은 남긴다.

### 4.2 접근성

명암(WCAG 2.1 상대 휘도로 계산):

| 글자 / 바탕 | 비 | 판정 |
|---|---|---|
| `--dim #8A8A8A` / `#000` | 6.08 | 4.5:1 통과 |
| `--dim #8A8A8A` / `--raise #262626` | 4.38 | 실패 → 이 바탕 위에서만 `#949494`(4.99, ANSI 246)로 다시 선언 |
| `--fg #C8C8C8` / `#000` | 12.55 | 통과 |
| `#000` / `--inv #C8C8C8` (반전) | 12.55 | 통과 |
| `#000` / `--y` (`.btn.ya`, DEV) | 15.14 | 통과 |
| `--r` / `#000`, / `#262626` | 7.05, 5.08 | 통과 |
| `--y` `--c` `--g` / `#000` | 15.14, 12.65, 12.10 | 통과 |
| `--frame #6E6E6E` 상자선 / `#000` | 4.12 | 비텍스트 3:1 통과 |
| `--line #4A4A4A` 구분선 / `#000` | 2.37 | 장식용이라 기준 밖. 정보를 이 선에만 싣지 않는다 |
| 입력칸 `--raise` / `#000` | 1.40 | 칸 모양만으로는 3:1 미달 → `inset 0 -1px var(--dim)` 밑줄(6.08)로 구분 |

규칙:
- 동작은 `<button>`, 이동은 `<a href>`다. `div`/`span`에 클릭을 걸지 않는다. 시안의 `.tr` div 격자 대신 `<table>`을 쓴다.
- 입력마다 `<label for>` 또는 감싸는 `<label>`, 묶음은 `fieldset/legend`. placeholder를 라벨로 쓰지 않는다.
- 장식 문자(`╡ ╞`, `[ ]`, `* `)는 CSS `content: "…" / ""`로 넣어 읽지 않게 한다. 대체 텍스트 문법을 모르는 브라우저를 위해 같은 선언을 대체 텍스트 없이 한 번 앞에 쓴다. 태그 기호 `[ok]`는 `aria-hidden` span이고 라벨을 함께 보인다.
- `:focus-visible { outline: 2px solid var(--y); outline-offset: 1px }`. 반전 바탕(제목 줄, 선택 메뉴, `.btn.rev`) 안에서는 노랑과 회색의 대비가 1.21이므로 `outline-color: var(--bg)`로 바꾼다.
- 현재 메뉴는 `aria-current="page"`이고 CSS도 이 속성으로 반전한다. 클래스와 속성을 따로 두지 않는다.
- 상태는 색만으로 전하지 않는다. 기호 + 한국어 라벨, 막대 옆 숫자.
- `prefers-reduced-motion` 블록은 남긴다(애니메이션은 없지만 브라우저 기본 전환을 막는다).
- 상자 제목은 `h2`, 화면 제목은 `h1` 하나. 제목 줄의 로고는 링크일 뿐 제목이 아니다.

## 5. 시안이 요구하는 UI 밖 작업

| # | 작업 | 필요한 것 | 크기 | 판정 |
|---|---|---|---|---|
| 1 | 단축키 `g d` / `g p` / `g s` | `base.html` `<head>` 인라인 스크립트 약 15줄: `keydown`, 입력칸 포커스·수식키 무시, `g` 뒤 1초 안의 키로 `a[data-g="키"]`의 `href`로 이동. 스크립트가 `<html>`에 `kbd` 클래스를 달고, 이 클래스가 없으면 `.k`와 키 캡을 숨긴다(점진적 향상) | 작음, 1커밋 | 구현 |
| 2 | 메뉴 개수(`.cn`)와 바닥 상태 줄 | `main.py`에서 `templates.context_processors.append(shell)`. `shell(request)`가 `{"shell": {"stale": 응답 없는 사이트 수, "running": bool, "next_run_at": …, "now": datetime.now()}}`를 돌려준다. `stale_before()`를 그대로 쓴다. `request.app.state`에 db가 없으면 빈 dict. 템플릿은 `shell` 없이도 그려져야 한다(테스트가 `get_template().render()`로 직접 그린다). 개수는 사이트 경고 하나만 둔다. 노랑 `.cn`은 "볼 것"이라는 뜻이라 프로그램 수 같은 일반 개수에는 쓰지 않는다 | 작음, 1커밋 | 구현 |
| 3 | 제목 줄 시각 | 2번의 `shell.now`를 `dt`로 렌더 시각으로 보인다. 초 단위로 가는 시계(JS)는 두지 않는다 | 작음, 2번에 포함 | 구현 |
| 4 | 상태 색 매핑을 CSS에서 `views.py` `TONE`으로 이동, `FLASH` 종류를 `ok`/`run`/`bad`/`none`으로 이름 바꿈(`started`, `already-running` → `run`) | `views.py` 몇 줄 | 작음, 컴포넌트 커밋에 포함 | 구현 |
| 5 | 행 커서 `j`/`k` + `Enter` | 현재 행 이동, 스크롤, 표마다 Enter의 뜻(링크 vs 행 안 폼), 행 안 폼 포커스와의 충돌 처리 | 중간 | 구현하지 않음. `base.html` 단축키 스크립트 위에 `{# 추가 작업: j/k 행 커서. tr.cur를 키로 옮기고 Enter로 행의 첫 링크를 연다 #}` |
| 6 | `?` 도움말 겹창 | 키 줄이 이미 모든 키를 보인다 | 작음 | 필요 없음. 하지 않는다 |
| 7 | 로그를 시안의 `.ln` 격자(시각 · 도구 · 내용 · 소요)로 | 실행 로그와 진단 진행 로그를 서버에서 줄 단위로 파싱하고, `doctor.py` htmx 조각과 `logmark`, 테스트를 함께 바꿔야 한다 | 중간 | 구현하지 않음. `run.html` 로그 상자 위에 `{# 추가 작업: 로그를 .ln 격자(시각/내용)로. logmark와 doctor_progress 조각을 함께 바꿀 것 #}` |
| 8 | 다운로드 날짜 그룹, 최근 실행 막대 | 이미 넘기는 `downloads`, `runs`로 템플릿에서 계산 | 없음 | 페이지 커밋에 포함 |

## 6. 구현 순서

각 커밋 뒤 공통 검증: `uv run pytest -q` 통과, `touch app/views.py`로 재시작 후 아래 curl. 커밋은 단위마다 따로 한다.

1. **토큰, base, 셸**
   파일: `app/static/app.css`(tokens, base, shell 구획 교체, light/dark 분기 삭제. 아직 안 바꾼 화면이 읽히도록 옛 토큰 이름을 새 값에 잇는 임시 별칭 블록 `/* 임시: 7번에서 삭제 */`), `app/templates/base.html`(글꼴, 제목 줄, crumb 블록, 메뉴 상자, dev 줄, 키 줄 정적 마크업).
   확인: `curl -s :8180/ | grep -c 'class="title"\|class="box side"\|class="keys"'`가 3, `fonts.googleapis.com` 포함, `pretendard` 없음, `/programs`에서 `aria-current="page"`가 프로그램 링크에 붙음.
2. **컴포넌트와 매크로**
   파일: `app.css`(components, utilities 구획), `_macros.html`(`box`, `tag`, `flash`, `empty`; `badge` 삭제), `app/views.py`(`TONE`, `FLASH` 종류), `badge`를 부르던 네 템플릿의 import와 호출을 `tag`로.
   확인: `curl -s :8180/runs/1 | grep -o 'class="tag [a-z]*"'`, `curl -s :8180/sites | grep -c '자동 변경됨'`(자동 변경 기록이 있으면 1 이상).
3. **단축키와 셸 데이터**(5장 1~3)
   파일: `base.html`(스크립트, `.cn`, 상태 줄, 시각, `추가 작업:` 주석), `app/main.py`(`shell` context processor).
   확인: `curl -s :8180/programs | grep -o 'data-g="[a-z]"'`가 셋, 키 줄 `.rt`에 `다음 실행` 또는 `실행 중`. 브라우저에서 `g s`가 `/sites`로 이동, 입력칸 안에서는 무시.
4. **대시보드** `index.html` (+ `app.css` pages `.stats`)
   확인: `curl -s :8180/ | grep -c 'class="box'`가 4 이상, `class="big"` 포함, `hide-sm` 없음. 폭 360px에서 가로 스크롤은 `.tw` 안에서만.
5. **프로그램** `programs.html`
   확인: `curl -s :8180/programs | grep -c 'class="chk"'`가 프로그램 수와 같음, `class="ck"` 포함, 삭제 `confirm(` 유지. 해상도 저장과 켜기 POST 후 303.
6. **사이트** `sites.html` (+ `.sites`)
   확인: `test_sites_page_url_changes` 통과, `curl -s :8180/sites | grep -c 'class="box'`가 사이트 수 이상, 수정 폼 저장 후 `?msg=applied`의 `.msg`.
7. **실행, 진단, 오류 + 정리** `run.html`, `doctor.html`, `error.html`, `app.css`(1번 임시 별칭과 옛 컴포넌트 CSS `.card` `.hero` `.badge` `.switch` `.table` `.diff` `.flash` `.empty` `.error-*` `.site-*` 삭제, 파일 머리 주석을 이 문서로), `run.html`의 `추가 작업:` 주석.
   확인: `curl -s :8180/runs/1 | grep -c 'class="big"'`, `curl -s :8180/nope`가 404와 `.box.bad`, `/doctor/<id>`에서 `id="progress" class="log"` 유지. `grep -nE 'card|badge|btn-(primary|secondary|ghost|danger)|is-(ok|warn|bad|run)' app/templates app/static/app.css`가 비어 있음.
