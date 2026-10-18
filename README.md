# torrent_web_scraper v2

등록한 TV 프로그램의 새 회차를 토렌트 게시판에서 찾아 Pi의 Transmission에 자동으로 추가하는 개인용 크롤러다. 사이트가 고장나면 Claude(Doctor)가 원인을 진단한다.

```
Mac (OrbStack)
└─ Docker container  ─  FastAPI + uvicorn (process 1개)
   ├─ Web UI (127.0.0.1:8080)
   ├─ Scheduler (asyncio, 주기는 런타임에 변경 가능)
   ├─ Crawler ── Playwright Chromium (--headless=new, ECH) ──→ 토렌트 사이트 3곳
   ├─ Doctor ─── Claude Agent SDK + 전용 진단 도구
   ├─ SQLite (/data/app.db, 호스트 ./data에 보존)
   └─ Transmission RPC ──→ Pi 192.168.0.10:59090
```

## 왜 이 구조인가

Pi(Raspbian 10, armv7)에서는 최신 도구를 쓸 수 없다. 그래서 크롤링은 Mac의 Docker에서 하고 Pi는 Transmission만 맡는다. 국내 SNI 차단 때문에 curl, requests 같은 일반 HTTP 클라이언트는 TLS 단계에서 끊긴다. ECH를 지원하는 Chromium `--headless=new`만 통과하고, Playwright 기본 headless shell은 ECH가 없어 실패한다.

## 설치와 실행

1. `.env.example`을 `.env`로 복사하고 값을 채운다(권한 600 권장).

| 키 | 설명 |
|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | Doctor용 Claude 인증. `ANTHROPIC_API_KEY`로 대신해도 된다(둘 중 하나). |
| `TRANSMISSION_URL` | Pi RPC 주소. 예: `http://192.168.0.10:59090/transmission/rpc` |
| `TRANSMISSION_USER`, `TRANSMISSION_PASSWORD` | Transmission RPC 계정 |

2. `docker compose up -d --build`
3. 브라우저에서 `http://127.0.0.1:8080`에 접속한다. 인증이 없으므로 이 Mac에서만 열린다.

`restart: unless-stopped`이므로 OrbStack이 다시 켜지면 컨테이너도 자동으로 뜬다.

**macOS 로컬 네트워크 권한**: 컨테이너가 LAN의 Pi에 닿으려면 시스템 설정 → 개인정보 보호 및 보안 → 로컬 네트워크에서 OrbStack을 켜고 OrbStack을 재시작해야 한다. 꺼져 있으면 실행 기록에 `transmission FAIL ... timed out`이 남고 상태가 `partial`이 된다. 이때 다운로드는 기록되지 않으므로 다음 실행에서 다시 시도한다.

## 화면

| 화면 | 내용 |
|---|---|
| 대시보드 `/` | 다음 실행 시각, 주기 변경, [지금 실행], 최근 실행과 다운로드 |
| 프로그램 `/programs` | 등록(이름 + 해상도 720p/1080p/무관), 켜기/끄기, 삭제 |
| 사이트 `/sites` | URL·게시판 수정, 켜기/끄기, [doctor](모델 선택), 최근 진단 판정 |
| 실행 상세 `/runs/{id}` | 로그 원문 |
| 진단 리포트 `/doctor/{id}` | 판정, 요약, 근거, 수정 제안과 [적용], 비용 |

## 크롤 규칙

- 켜진 사이트의 게시판 첫 페이지만 본다.
- 제목에 프로그램 이름의 모든 단어가 들어 있고(대소문자 무시) 해상도가 맞으면 매칭이다. 여러 프로그램이 맞으면 목록 순서상 첫 번째가 이긴다.
- 회차 키는 제목의 `E823.261011` 형식(날짜가 없으면 `E12`)이다.
- 같은 해시나 같은 (프로그램, 회차)는 한 번만 추가한다. 같은 회차가 여러 사이트에 올라와도 하나만 받는다. 회차 키가 없는 글은 해시로만 중복을 막는다.
- 사이트 첫 게시판이 실패하거나 글이 0개면 도메인 번호를 +1..+5까지 바꿔 보고, 글이 나오는 도메인으로 사이트 URL을 갱신한다.
- 상태: 모두 성공이면 `ok`, 일부 실패면 `partial`, 성공한 사이트가 없으면 `error`.

## 스케줄

- 기본 주기는 60분이고 대시보드에서 분 단위(1..1440)로 바꾸면 바로 반영된다.
- 다음 실행은 마지막 실행 시작 시각 + 주기다. DB에 실행 기록이 없으면 바로 실행하고, 재시작만으로는 추가 실행하지 않는다.
- Mac이 잠자는 동안에는 돌지 않는다. 깨어난 뒤 예정 시각이 지났으면 60초 안에 실행한다.

## Doctor

| 판정 | 의미 |
|---|---|
| `ok` | 정상 |
| `domain_moved` | 도메인 이전 |
| `blocked` | 차단 |
| `site_down` | 사이트 다운 |
| `cloudflare` | Cloudflare 사람 인증 필요 |
| `parser_broken` | 사이트는 정상인데 파서가 실패 |

- 도구는 직접 만든 읽기 전용 4개뿐이다: `dns_tls_check`, `browse`, `run_parser`, `probe_domains`. 내장 WebFetch, Bash 등은 막는다(SNI 차단에 걸려 오판하기 때문).
- 모델은 별칭 `sonnet`(기본) 또는 `opus`로 지정해 항상 최신을 쓴다.
- 실행당 최대 15턴, 비용 상한 $1.
- 수정 제안은 자동 반영하지 않는다. 리포트의 [적용] 버튼을 눌러야 사이트 설정이 바뀐다.
- Chromium은 크롤링과 Doctor가 lock을 공유해서 동시에 하나만 뜬다.

## 데이터

`./data/app.db`(SQLite, 컨테이너의 `/data`). 테이블은 6개다.

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
- 프로그램 17개: v1 Pi 규칙을 가져왔다. 놀면 뭐하니와 라디오스타만 켜져 있다.

## 개발

```sh
uv sync
uv run pytest -q                                                     # 네트워크 없이 fixture로 테스트
docker compose run --rm scraper python -m app.scheduler --dry-run   # 실제 크롤링, Transmission 추가는 안 함
docker compose logs -f
```

dry-run은 Transmission 추가와 사이트 URL 변경을 하지 않지만 실행 기록은 남기므로, 다음 정기 실행 시각이 그만큼 뒤로 밀린다. 스케줄에 맞춰 돌아야 할 때는 실행하지 않는다.

## 범위 밖

사용자 인증과 외부 노출, 알림, 페이지네이션, 사이트별 전용 파서, Doctor 자동 수정, Pi에서의 실행, Cloudflare 사람 인증 우회.

## v1 소개

[Torrent_web_scraper: 토렌트 자동 다운로드 프로젝트 소개/설치](https://devinlife.com/project%20torrnet_web_scraper/torrent-web-scraper/)
