# 크롤러 리서치: 5개 사이트 실측 (2026-10-18)

Fixture: `tests/fixtures/<site_key>/{board,detail}.html`. 크기가 모두 90 KB 미만이어서 script/style을 제거하지 않았습니다. `page.content()`는 `domcontentloaded` 후 2초 대기한 시점에 저장했습니다.
detail.html은 5곳 모두 같은 글인 **`놀면 뭐하니.E348.261017.720p-NEXT`**입니다. 라디오스타는 어느 사이트의 첫 페이지에도 없었습니다.

## 1. 실행 방법 (5곳 모두 첫 시도에 성공)

```python
# image: mcr.microsoft.com/playwright/python:v1.48.0-noble  (Chromium 130.0.6723.31)
b = p.chromium.launch(headless=False, args=["--headless=new", "--no-sandbox"])
ctx = b.new_context(locale="ko-KR")
resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
page.wait_for_timeout(2000)
html = page.content()
```

- 이미지에는 브라우저만 있고 **Python `playwright` 패키지가 없습니다.** 앱 Dockerfile은 `uv sync`로 설치하므로 문제가 없습니다. 임시 스크립트를 돌릴 때는 `pip install --target <dir> playwright==1.48.0`과 `PYTHONPATH`가 필요합니다.
- `--no-sandbox`는 사실상 중복입니다. Playwright가 기본값(`chromium_sandbox=False`)으로 이미 붙입니다. `channel=`은 필요 없었습니다.
- 페이지 하나에 2.4–3.5초 걸립니다. 이 값에는 2초 대기가 포함되어 있으므로 실제 로드는 약 0.5–1.5초입니다. 컨테이너 기동부터 페이지 5개 조회까지 총 17초였습니다.
- 사이트 23개 URL이 모두 attempt 1에 200을 반환했고 재시도는 없었습니다. ERR_CONNECTION_CLOSED는 옛 도메인(`torrentsome267.com`)에서만 3회 연속 발생했습니다. 이전 도메인이 SNI 차단된 상태로 보입니다(Doctor의 `blocked`/`domain_moved` 판정 참고).
- `http://` 접속은 `307` 후 `https://` 같은 경로, `200`으로 이어집니다(some, tt에서 확인). Chrome 내부의 HTTPS 업그레이드일 수 있으며, 서버 리다이렉트인지는 검증하지 않았습니다.
- **Cloudflare**: 5곳 모두 `cloudflareinsights` beacon만 있고, 챌린지(`cf-chl`, turnstile)는 없습니다. 상태 코드는 전부 200입니다.

## 2. 게시판

| site key | 예능 (확인) | 드라마 (한국드라마) | 시사/다큐 (다큐·교양) | 엔진 |
|---|---|---|---|---|
| torrentsome | `/v-4-16` 예능·오락 | `/v-2-13` 한국드라마 | `/v-4-17` 다큐·교양 | A |
| torrentrj | `/v-4-16` 예능·오락 | `/v-2-13` 한국드라마 | `/v-4-17` 다큐·교양 | A |
| torrentzota | `/t/4/16.html` 예능·오락 | `/t/2/13.html` 한국드라마 | `/t/4/17.html` 다큐·교양 | A 변형 |
| torrenttt | `/c/4` 영상·음악 (하위: `/c/4/16` 예능·오락) | `/c/2/13` 한국드라마 | `/c/4/17` 다큐·교양 | B |
| torrentbam | `/c/4` 영상·음악 (하위: `/c/4/16` 예능·오락) | `/c/2/13` 한국드라마 | `/c/4/17` 다큐·교양 | B |

- 위 경로는 모두 실제로 열어서 200과 올바른 `<title>`을 확인했습니다. "시사"라는 게시판은 없고, 그것이 알고 싶다·PD수첩류는 **다큐·교양**에 올라옵니다.
- 엔진 B의 `/c/4`는 영상·음악 전체(예능, 다큐, 음악 MP3)를 합친 게시판입니다. 첫 페이지 20건에 다큐와 음악 글이 섞이므로, 예능은 `/c/4/16`이 더 깊이 볼 수 있습니다. 그래서 B도 A와 똑같이 `16/13/17` 세 개를 씁니다.
- 페이지네이션은 `?page=N` 형식입니다(A: `/v-4-16?page=2`, 좋다: `/t/4/16.html?page=2`).

### 게시글 링크

| 엔진 | href 형식 (실측) | 비고 |
|---|---|---|
| A (some, rj) | `/v/311439` (상대경로, 숫자 id) | **some과 rj는 글 id가 같습니다** (`/v/311439`, `/topic/download/362601`). 백엔드가 같습니다 |
| A 변형 (zota) | `/torrent/r6o77rg.html` (상대경로, 소문자와 숫자) | **함정**: 카테고리 링크가 `/t/4.html`, `/t/2.html`이므로 B의 `/t/…\.html`과 겹칩니다 |
| B (tt, bam) | `https://torrenttt253.top/t/mP9XVQ.html` (**절대 URL**, 대소문자 섞인 5–6자 slug) | 광고는 `/ad/N` |

범용 정규식입니다. `urljoin(board_url, href)`를 적용한 결과에 사용하며, 5곳 23페이지에서 오탐이 0건이었습니다.

```python
POST_RE = re.compile(r'/(?:v/\d+|torrent/[a-z0-9]+\.html|t/(?!\d+\.html)[A-Za-z0-9]+\.html)$')
```

### 제목 추출

**모든 게시글 `<a>`에 `title` 속성이 있고, 그 값이 깨끗한 원제입니다.** 따라서 `a.get("title") or a.get_text(" ", strip=True)`를 쓰면 됩니다.
- 텍스트를 그대로 쓰면 썸은 장식이 붙습니다. 목록에서는 `<span class="badge">예능·오락</span>`이 들어가 `"예능·오락 전지적 참견 시점.E421…"`이 되고, 사이드바에서는 `"[예능·오락] 전지적 참견 시점…"`이 됩니다. 나머지 4곳은 텍스트와 title이 같습니다.
- 댓글 수(`[N]`), 날짜 접미사, 말줄임은 없습니다. 말줄임은 CSS `truncate`로만 처리되어 DOM에는 원문이 그대로 남습니다.
- `title` 속성만으로 게시글을 판별하면 안 됩니다. 광고(`/adver-472.html` title=`sm-728`, `t.me/…` title=`1`)에도 title이 있으므로 반드시 `POST_RE`를 같이 씁니다.

### 목록 구성, 정렬, 건수

| site | 본문 목록 | 첫 페이지 본문 | POST_RE 매칭 (사이드바 포함, 고유 URL) | 날짜 범위 (예능) |
|---|---|---|---|---|
| torrentsome | `div.topic-item > div > a[title]` | 20건 | 42 | 10/16–10/17 |
| torrentrj | `a.text-black.hover:text-red-500` | 20건 | 37 | 같음 |
| torrentzota | `div.topic-item a.item-link` | 20건 | 49 | 같음 |
| torrenttt | `a.text-black.hover:text-red-500` | 20건 | 50 | 같음 (`/c/4`) |
| torrentbam | `a.hover:underline.hover:text-blue-500` (인기자료 10건도 같은 class) | 20건 | 30 | 같음 (`/c/4`) |

- 정렬은 **최신순**입니다. A는 id 내림차순(311453, 311452, 311450…)이고 B는 날짜 내림차순입니다.
- 사이드바(TOP10, 인기자료, 최근글)에는 **다른 게시판의 글**(한국드라마, 영화, 다큐)과 오래된 글(10/11)이 섞여 있습니다. 범용 파서가 이 글들까지 매칭해도 해롭지 않습니다. URL로 중복을 제거하고, 회차와 해시 중복 방지로 처리합니다.
- 실제 제목 예 (각 사이트, 그대로 인용):
  - some: `전지적 참견 시점.E421.261017.720p-NEXT`, `우주떡집.최종.E12.1080p.H264.AAC.VIU.WEB-DL-LoveBug`, `2026 ABC 투어 in 냐짱.E01.261016.720p-NEXT`
  - rj: `살림하는 남자들 시즌2.E465.261017.720p-NEXT`, `영화가 좋다.E1026.261017.720p-NEXT`, `신랑수업 2.E30.261016.720p-NEXT`
  - zota: `놀면 뭐하니.E348.261017.720p-NEXT`, `무엇이든 해줄지니 비서진.E07.261016.720p-NEXT`, `100일의 거짓말 E01 1080p WEB H264-KBBQ`
  - tt: `그것이 알고 싶다.E1508.261017.720p-NEXT`, `2026년 09월 19일 신곡 [MP3]`, `특파원 보고 세계는 지금.E470.261017.720p-NEXT`
  - bam: `런닝맨.E823.261011.720p-NEXT`, `벅스(Bugs) 2026년 10월 01일 실시간 TOP 100 [FLAC+MP3]`, `나 혼자 산다.E669.261016.720p-NEXT`

## 3. 상세 페이지와 magnet

| site | magnet href (그대로) | 개수 | 주변 요소 |
|---|---|---|---|
| torrentsome | `magnet:?xt=urn:btih:4e4d86cbee91db107def6d3fd24271afd28130e2` | 1 | `다운로드` → `/topic/download/362601` (.torrent) |
| torrentrj | `magnet:?xt=urn:btih:4e4d86cbee91db107def6d3fd24271afd28130e2` | 1 | `다운로드` → `/topic/download/362601` |
| torrentzota | `magnet:?xt=urn:btih:4e4d86cbee91db107def6d3fd24271afd28130e2` | 1 (`target="_blank"`, 링크 텍스트가 해시) | `다운로드` → `/down/362541.html` |
| torrenttt | `magnet:?xt=urn:4e4d86cbee91db107def6d3fd24271afd28130e2` | 1 | `다운로드` → `https://dc.filesbest.xyz/download/1orV5r/2` |
| torrentbam | `magnet:?xt=urn:4e4d86cbee91db107def6d3fd24271afd28130e2` | 1 | `다운로드` → `https://dc.filesbest.xyz/download/Yegozg/3` |

- **엔진 B 형식은 정확히 `magnet:?xt=urn:` 바로 뒤에 소문자 hex 40자**입니다. `btih:`가 없고 `&dn=`, `&tr=`도 없습니다. A의 형식도 `xt` 하나뿐이고 `dn`/`tr`이 없습니다.
- 다른 `magnet:` href(광고 등)는 없습니다. 광고는 `/ad/N`, `/adver-N.html`, 텔레그램 링크입니다.
- **함정: 페이지 본문에 40자 hex가 따로 더 있습니다.** 포스터 이미지 파일명(`/uploadfile/full/a916eee9d8200653ab4ea1bffb069ab218c71eb7.jpg`, JSON-LD `image`)이고, 좋다는 사이드바 썸네일 10여 개도 hex 파일명입니다. 그래서 **해시는 `href^="magnet:"`에서만 뽑아야 합니다.** 페이지 전체를 hex로 스캔하면 안 됩니다.
- 상세 페이지에도 같은 프로그램의 옛 회차 목록이 있습니다(예: `/v/66177` `놀면 뭐하니.E01.190727.720p-NEXT`). 상세 페이지에서는 게시글 링크를 파싱하지 않습니다.

```python
MAG_RE = re.compile(r'^magnet:\?xt=urn:(?:btih:)?([0-9A-Fa-f]{40})\b')
info_hash = MAG_RE.match(href)[1].lower()
magnet = f"magnet:?xt=urn:btih:{info_hash}"   # Transmission에는 정규화한 형식으로 보냅니다
```

base32(32자) 해시는 관찰되지 않았습니다.

## 4. 제목 규칙과 회차 키

수집한 고유 제목 105개(전 게시판)의 집계입니다.
- 해상도: `720p` 78, `1080p` 24, `2160p` 1. `720P` 같은 대문자 표기는 **없습니다.** 비교는 소문자로 하면 충분합니다.
- 릴리즈 그룹: `-NEXT` 78건(TV 방송 녹화본은 전부 720p NEXT), `-Phanteam` 5, `-KBBQ` 2, `-Sniper` 2, `-LoveBug` 1, 그 밖에 영화 그룹들입니다.
- 회차: TV 방송분은 `.E\d{1,4}.\d{6}.` 형식입니다(`E00`, `E02`, `E1508` 모두 존재). 날짜는 방영일 `YYMMDD`입니다. WEB-DL(OTT) 릴리즈에는 날짜가 없습니다(`E12.1080p`, 공백 구분 `E01 1080p`). 소문자 `e01`이나 다중 회차(`E01-E02`)는 관찰되지 않았습니다.
- 시즌 숫자는 제목 안에 공백 뒤에 붙습니다(`신인감독 김연경 2.E01`, `신랑수업 2.E30`). 날짜가 없는 WEB-DL은 시즌이 달라도 키가 `E01`로 같으므로, 같은 프로그램 이름 규칙에서는 충돌할 수 있습니다. 현재 대상 17개 프로그램은 전부 NEXT 날짜형이라 실질적인 문제는 없습니다.

```python
EP_RE = re.compile(r'(?<![A-Za-z0-9])E(\d{1,4})(?:\.(\d{6}))?(?!\d)')
def episode_key(t):
    m = EP_RE.search(t)
    return m and (f"E{m[1]}.{m[2]}" if m[2] else f"E{m[1]}")
```

| site | 제목 | 키 |
|---|---|---|
| torrentsome | `런닝맨.E823.261011.720p-NEXT` | `E823.261011` |
| torrentsome | `영화가 좋다.E1026.261017.720p-NEXT` | `E1026.261017` |
| torrentzota | `접속 무비월드.E00.261017.720p-NEXT` | `E00.261017` |
| torrentzota | `100일의 거짓말 E01 1080p WEB H264-KBBQ` | `E01` |
| torrenttt | `그것이 알고 싶다.E1508.261017.720p-NEXT` | `E1508.261017` |
| torrenttt | `신인감독 김연경 2.E01.261011.720p-NEXT` | `E01.261011` |
| torrentrj | `우주떡집.최종.E12.1080p.H264.AAC.VIU.WEB-DL-LoveBug` | `E12` |
| torrentrj | `연애박사.Between Steps.E04.1080p.DSNP.WEB-DL.AAC.2.0-Sniper` | `E04` |
| torrentbam | `냉장고를 부탁해 since 2014.E92.261011.720p-NEXT` | `E92.261011` |
| torrentbam | `놀면 뭐하니.E348.261017.720p-NEXT` | `E348.261017` |
| torrenttt | `호프 Hope (2026) (1080p AMZN WEB-DL x265 10bit EAC3 5.1 Korean Silence)` | `None` (`EAC3` 오탐 없음) |
| torrentbam | `벅스(Bugs) 2026년 10월 01일 실시간 TOP 100 [FLAC+MP3]` | `None` |

## 5. 사이트 간 중복 (de-dup 테스트용)

`놀면 뭐하니.E348.261017.720p-NEXT`가 **5곳 모두**에 같은 제목으로 올라와 있고, **info hash도 5곳 모두 `4e4d86cbee91db107def6d3fd24271afd28130e2`로 같습니다.**

| site | 상세 URL |
|---|---|
| torrentsome | https://torrentsome268.com/v/311439 |
| torrentrj | https://torrentrj274.com/v/311439 |
| torrentzota | https://torrentzota206.com/torrent/r6o77rg.html |
| torrenttt | https://torrenttt253.top/t/mP9XVQ.html |
| torrentbam | https://torrentbam252.top/t/1BeK5b.html |

이 fixture들만으로 해시 중복(PK)과 회차 중복(`E348.261017`)을 함께 테스트할 수 있습니다. 첫 페이지 목록도 5곳이 사실상 같습니다(같은 업로드 피드를 미러링). 엔진이 셋이라 **파서 장애에는 분산 효과가 있지만, 콘텐츠 출처는 하나**입니다.
