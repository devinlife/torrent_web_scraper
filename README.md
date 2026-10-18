# torrent_web_scraper

등록한 TV 프로그램의 새 회차를 토렌트 게시판에서 찾아 Pi의 Transmission에 자동으로 추가하는 개인용 크롤러다. 사이트가 고장나면 Claude(Doctor)가 원인을 진단한다.

```
Mac (OrbStack)
└─ Docker container  ─  FastAPI + uvicorn (process 1개)
   ├─ Web UI (prod 127.0.0.1:8080, dev 127.0.0.1:8081, 포트는 .env로 변경)
   ├─ Scheduler (asyncio, 주기는 런타임에 변경 가능)
   ├─ Crawler ── Playwright Chromium (--headless=new, ECH) ──→ 토렌트 사이트 3곳
   ├─ Doctor ─── Claude Agent SDK + 전용 진단 도구
   ├─ SQLite (/data/app.db, 호스트 ./data/<env>에 보존)
   └─ Transmission RPC ──→ Pi 192.168.0.10:59090
```

## 왜 이 구조인가

Pi(Raspbian 10, armv7)에서는 최신 도구를 쓸 수 없다. 그래서 크롤링은 Mac의 Docker에서 하고 Pi는 Transmission만 맡는다. 국내 SNI 차단 때문에 curl, requests 같은 일반 HTTP 클라이언트는 TLS 단계에서 끊긴다. ECH를 지원하는 Chromium `--headless=new`만 통과하고, Playwright 기본 headless shell은 ECH가 없어 실패한다.

이미지는 `python:3.12.15-slim-bookworm` 위에 멀티 스테이지로 만든다. 빌드 단계에서 uv로 `.venv`를 만들고, 실행 단계에는 `.venv`와 `app/`만 복사한 뒤 `playwright install --with-deps chromium`으로 전체판 Chromium과 그 시스템 라이브러리만 설치한다(`/ms-playwright`). Firefox, WebKit, uv는 넣지 않는다. 크기는 약 1.5GB이고, 대부분 Chromium(약 590MB)과 Doctor가 쓰는 Claude Code 실행 파일이 든 claude-agent-sdk(약 230MB)다. dev와 prod는 같은 Dockerfile을 쓴다. Alpine은 Playwright Chromium이 musl을 지원하지 않아 쓸 수 없다.

## 설치와 실행

1. `.env.example`을 `.env`로 복사하고 값을 채운다(권한 600 권장).

| 키 | 설명 |
|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | Doctor용 Claude 인증. `ANTHROPIC_API_KEY`로 대신해도 된다(둘 중 하나). |
| `TRANSMISSION_URL` | Pi RPC 주소. 예: `http://192.168.0.10:59090/transmission/rpc` |
| `TRANSMISSION_USER`, `TRANSMISSION_PASSWORD` | Transmission RPC 계정 |
| `PROD_PORT`, `DEV_PORT` | 웹 UI 포트(127.0.0.1). 기본 8080, 8081 |

2. `./server.sh prod up`
3. 브라우저에서 `http://127.0.0.1:8080`(`PROD_PORT`)에 접속한다. 인증이 없으므로 이 Mac에서만 열린다.

## 서버 구동

서버는 dev와 prod 두 가지이고, 둘 다 Mac의 Docker에서 돈다. 각각 별도의 compose 프로젝트, 포트, DB를 쓰므로 동시에 띄워도 서로 영향이 없다.

| | dev | prod |
|---|---|---|
| 주소 | http://127.0.0.1:8081 (`DEV_PORT`) | http://127.0.0.1:8080 (`PROD_PORT`) |
| compose 파일 | `compose.dev.yaml` (프로젝트 `torrent_web_scraper-dev`) | `compose.yaml` (프로젝트 `torrent_web_scraper`) |
| DB | `./data/dev/app.db` | `./data/prod/app.db` |
| 크롤링 | 모든 실행이 dry-run. Transmission 추가, 다운로드 기록, 사이트 URL 변경, `last_ok_at` 갱신을 하지 않는다 | Transmission에 실제로 추가한다 |
| 코드 반영 | `./app`을 마운트하고 `uvicorn --reload`로 저장 즉시 재시작 | 이미지에 굽는다. 코드를 바꾸면 `up`으로 재빌드 |
| 재부팅 | 자동으로 뜨지 않는다 | `restart: unless-stopped`이라 OrbStack이 켜지면 자동으로 뜬다 |
| 화면 표시 | 상단에 `DEV · dry-run` 배지, 탭 제목에 `[dev]` | 표시 없음 |

### 명령

```sh
./server.sh <dev|prod> <command>
```

| 명령 | 동작 |
|---|---|
| `up` | 이미지를 빌드하고 백그라운드로 띄운다 |
| `down` | 컨테이너를 내린다. DB는 남는다 |
| `restart` | 컨테이너를 재시작한다(재빌드 없음) |
| `reset` | 내리고 DB를 지운 뒤 다시 띄운다. 시드 데이터로 새로 시작한다. prod는 `prod`를 입력해야 진행한다 |
| `logs` | 로그를 따라 본다 |
| `ps` | 컨테이너 상태를 본다 |
| `dry-run` | 크롤링을 한 번 실행하고 로그를 출력한다. Transmission 추가와 URL 변경은 하지 않는다 |

새 DB로 시작하면 첫 크롤링이 바로 돈다. prod를 `reset`하면 다운로드 기록이 사라지므로 게시판 1~N쪽에 남은 회차를 다시 추가하려 한다(이미 Transmission에 있는 토렌트는 `duplicate`로 기록된다).

### 환경 구분

환경은 `APP_ENV`(`dev` | `prod`) 하나로 정하고, compose 파일이 값을 넣는다. 다른 값이면 앱이 시작하지 않는다. 값이 없으면 `dev`로 본다. 설정이 빠졌을 때 실제 다운로드가 일어나지 않게 하기 위해서다. `app/config.py`가 `APP_ENV`에서 `DRY_RUN`을 정하고, 스케줄러와 `python -m app.scheduler`가 그 값을 따른다. 비밀값은 두 환경이 같은 `.env`를 쓴다.

**macOS 로컬 네트워크 권한**: 컨테이너가 LAN의 Pi에 닿으려면 시스템 설정 → 개인정보 보호 및 보안 → 로컬 네트워크에서 OrbStack을 켜고 OrbStack을 재시작해야 한다. 꺼져 있으면 실행 기록에 `transmission FAIL ... timed out`이 남고 상태가 `partial`이 된다. 이때 다운로드는 기록되지 않으므로 다음 실행에서 다시 시도한다.

## 화면

| 화면 | 내용 |
|---|---|
| 대시보드 `/` | 상태 카드(마지막 실행 결과, 다음 실행, 주기 [저장]), [지금 실행](실행 중엔 10초마다 자동 갱신), 통계 타일 4개, 최근 실행과 다운로드 표 |
| 프로그램 `/programs` | 등록(이름 + 해상도 720p/1080p 복수 선택, 안 고르면 무관), 등록 후 해상도 수정(행의 해상도 버튼), 켜기/끄기 스위치, 삭제(확인 후). 위에 있을수록 먼저 매칭된다 |
| 사이트 `/sites` | 사이트마다 가로 카드 하나(한 열): URL(새 탭), 켜기/끄기 스위치, 최근 성공(주기의 3배 넘게 없으면 `응답 없음` 경고와 주황 띠), 최근 진단 판정, [진단 · 최대 $1](경고 카드에서만 강조), [수정] 인라인 편집기. 머리 오른쪽에 진단 모델 설정 |
| 실행 상세 `/runs/{id}` | 상태, 시작·소요·매칭·추가, 로그(`FAIL`/`error` 줄 강조) |
| 진단 리포트 `/doctor/{id}` | 판정 카드와 요약, 현재/제안 비교(바뀐 칸 강조)와 [이 설정으로 변경], 근거, 진행 로그(진행 중엔 2초마다 갱신, 끝나면 접힘), 모델과 비용 |

상태는 한국어 배지(원시값은 툴팁)로, 시각은 날짜를 붙여 `10-18 19:23 · 42분 전`처럼(지난해는 `2025-10-18 19:23`) 보인다. 삭제와 사이트 설정 변경은 확인 창을 거친다. 진단(최대 $1)은 누르면 바로 시작한다.

스타일은 빌드 없는 CSS 파일 하나(`app/static/app.css`, `/static`으로 제공)다. 다크 모드는 OS 설정을 따른다. 글꼴은 Pretendard를 jsDelivr CDN에서 불러오고, 못 불러오면 시스템 글꼴(Apple SD Gothic Neo 등)로 대체된다. JS는 진단 화면의 htmx와 확인 창뿐이다. 휴대폰 폭(720px 이하)에서는 nav가 둘째 줄로 내려가고 카드와 표가 한 열로 쌓인다.

## 크롤 규칙

- 켜진 사이트의 게시판마다 1~N쪽(`?page=N`)을 본다. N은 사이트 화면에서 사이트별로 정한다(1~10, 기본 3). 2쪽 이후를 못 읽어도 실패로 치지 않는다.
- 제목에 프로그램 이름의 모든 단어가 들어 있고(대소문자 무시) 선택한 해상도 중 하나라도 제목에 있으면 매칭이다. 무관이면 해상도를 보지 않는다. 여러 프로그램이 맞으면 목록 순서상 첫 번째가 이긴다.
- 회차 키는 제목의 `E823.261011` 형식(날짜가 없으면 `E12`)이다.
- 같은 해시나 같은 (프로그램, 회차)는 한 번만 추가한다. 같은 회차가 여러 사이트에 올라와도 하나만 받는다. 회차 키가 없는 글은 해시로만 중복을 막는다.
- 사이트 첫 게시판이 실패하거나 글이 0개면 도메인 번호를 +1..+5까지 바꿔 보고, 글이 나오는 도메인으로 사이트 URL을 갱신한다.
- 같은 사이트(호스트)에 연달아 요청할 때는 2~5초 무작위로 쉬고 요청한다. Doctor 도구 요청도 같다.
- 이미지·폰트·미디어 요청은 막는다(사이트 부하와 크롤링 시간 절감). CSS와 JS는 그대로 받는다.
- 상태: 모두 성공이면 `ok`, 일부 실패면 `partial`, 성공한 사이트가 없으면 `error`.

## 스케줄

- 기본 주기는 60분이고 대시보드에서 분 단위(5..1440)로 바꾸면 바로 반영된다.
- 다음 실행은 마지막 실행 시작 시각 + 주기다. DB에 실행 기록이 없으면 바로 실행하고, 재시작만으로는 추가 실행하지 않는다.
- Mac이 잠자는 동안에는 돌지 않는다. 깨어난 뒤 예정 시각이 지났으면 60초 안에 실행한다.

## Doctor

| 판정 | 의미 |
|---|---|
| `ok` | 정상 |
| `domain_moved` | 도메인 이전 |
| `blocked` | 차단 |
| `site_down` | 사이트 다운 |
| `transient` | 일시 장애 (지금은 접속 안 되지만 최근 크롤링은 성공) |
| `cloudflare` | Cloudflare 사람 인증 필요 |
| `parser_broken` | 사이트는 정상인데 파서가 실패 |

- 도구는 직접 만든 읽기 전용 4개뿐이다: `dns_tls_check`, `browse`, `run_parser`, `probe_domains`. 내장 WebFetch, Bash 등은 막는다(SNI 차단에 걸려 오판하기 때문).
- 모델은 별칭 `sonnet`(기본) 또는 `opus`로 지정해 항상 최신을 쓴다.
- 실행당 최대 15턴, 비용 상한 $1.
- `browse`는 연결 끊김(`ERR_CONNECTION_CLOSED`/`RESET`)이면 5·10·15초 간격으로 다시 시도한다. ECH 설정이 늦게 와서 잠깐 평문 SNI로 붙는 일시 실패를 차단으로 오판하지 않기 위해서다.
- 수정 제안은 자동 반영하지 않는다. 리포트의 [이 설정으로 변경] 버튼을 눌러야 사이트 설정이 바뀐다.
- Chromium은 크롤링과 Doctor가 lock을 공유해서 동시에 하나만 뜬다.

## 데이터

`./data/<env>/app.db`(SQLite, 컨테이너의 `/data`). 테이블은 6개다.

| 테이블 | 내용 |
|---|---|
| `programs` | 등록한 프로그램(이름, 해상도, 켜기) |
| `sites` | 사이트 URL, 게시판 목록, 켜기, 마지막 성공 시각 |
| `settings` | `interval_min`, `doctor_model` |
| `runs` | 실행 기록(상태, 매칭/추가 건수, 로그) |
| `downloads` | 추가한 해시와 회차(중복 방지 기준) |
| `doctor_reports` | 진단 리포트(판정, JSON, 비용, 진행 로그) |

초기 데이터는 테이블이 비어 있을 때만 들어간다.

- 사이트 5곳: 토렌트썸, 토렌트좋다, 토렌트티티(켬), 토렌트알지, 토렌트밤(끔, 예비). 게시판은 사이트마다 예능·오락, 한국드라마, 다큐·교양 3개.
- 프로그램 17개. 놀면 뭐하니와 라디오스타만 켜져 있다.

## 개발

```sh
uv sync
uv run pytest -q          # 네트워크 없이 fixture로 테스트
./server.sh dev up        # 코드 수정은 ./app 저장만으로 반영된다
./server.sh dev logs
```

prod에서 `dry-run`을 실행하면 실행 기록이 prod DB에 남으므로 다음 정기 실행 시각이 그만큼 뒤로 밀린다. 크롤링을 확인할 때는 dev를 쓴다.

## 범위 밖

사용자 인증과 외부 노출, 알림, 사이트별 전용 파서, Doctor 자동 수정, Pi에서의 실행, Cloudflare 사람 인증 우회.
