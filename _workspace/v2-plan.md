# torrent_web_scraper v2 기획안

작성일: 2026-10-18 · 브랜치: `refactor/fastapi-docker`

## 1. 목표

Mac의 Docker에서 실행되는 웹 서비스입니다. 등록한 TV 프로그램의 새 회차를 토렌트 사이트에서 찾아 Pi의 Transmission에 자동으로 추가합니다. 사이트가 고장나면 Claude가 원인을 진단합니다.

- **v1의 문제**: 2025-10-13 이후 다운로드가 한 건도 없습니다. 원인은 세 가지입니다.
  - torrentsir 도메인이 사라졌습니다.
  - 국내 SNI 차단으로 스크립트가 사이트에 접속하지 못합니다.
  - Pi가 Raspbian 10 Buster(armv7 32bit)라서 최신 도구를 쓸 수 없습니다.
- **v2의 방향**: 크롤링은 Mac에서 하고 Pi는 다운로드(Transmission)만 합니다. 설정과 기록은 코드 수정 대신 웹 화면에서 관리합니다.

## 2. 검증된 사실 (2026-10-18 실측)

| 항목 | 결과 |
|---|---|
| 사이트 11곳 점검 | 스크립트로 접근 가능한 곳은 5곳(썸, 알지, 좋다, 티티, 밤)입니다. 나머지는 차단, Cloudflare 사람 인증, 로그인 필요, 접속 불가입니다. 부록 A 참고. |
| SNI 차단 우회 | 일반 HTTP 클라이언트(curl, urllib, requests)는 TLS 단계에서 연결이 끊깁니다. ECH를 지원하는 Chromium(`--headless=new`)으로는 성공합니다. Docker 컨테이너 안에서도 성공했습니다. Playwright 기본 headless shell은 ECH가 없어 실패합니다. |
| 대상 사이트 | 토렌트썸, 토렌트좋다, 토렌트티티. 예비로 알지와 밤을 둡니다. 세 곳의 엔진 구조가 서로 달라서 한 엔진이 막혀도 나머지가 버팁니다. |
| 범용 파싱 | 게시판에서 제목 매칭 → 상세 페이지의 `magnet:` 링크 → 해시를 정규화하는 로직 하나로 5곳 모두 동작했습니다. |
| Transmission | Mac에서 Pi `192.168.0.10:59090`으로 RPC 인증과 세션 획득(`session-get`)까지 성공했습니다. |
| Claude Agent SDK | 컨테이너(linux/arm64)에서 `CLAUDE_CODE_OAUTH_TOKEN`으로 동작합니다. 별칭 `sonnet`은 claude-sonnet-5-5로, `opus`는 claude-opus-5-5로 연결되어 항상 최신 모델을 씁니다. |

## 3. 시스템 구성

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

- 크롤링과 Doctor는 브라우저 lock을 공유해서 Chromium이 동시에 하나만 뜨게 합니다.
- 스케줄러는 `asyncio` task이고, 주기를 바꾸면 `asyncio.Event`로 깨워서 바로 반영합니다.

## 4. 제품 기능

| ID | 기능 | 설명 |
|---|---|---|
| F1 | 프로그램 등록 | 프로그램 이름과 해상도(720p / 1080p / 무관)를 입력합니다. 켜기/끄기와 삭제를 할 수 있습니다. |
| F2 | 자동 크롤링 | 정해진 주기마다 켜진 사이트들의 게시판 첫 페이지를 확인합니다. 제목의 모든 단어가 들어 있고 해상도가 맞으면 magnet을 추출합니다. |
| F3 | 중복 방지 | 같은 해시나 같은 회차(예: `E823.261011`)는 한 번만 추가합니다. 같은 회차가 3개 사이트에 다 올라와도 하나만 받습니다. |
| F4 | Transmission 전송 | Pi에 RPC로 추가합니다. 세션 ID 갱신(409)을 처리합니다. |
| F5 | 주기 변경 | 대시보드에서 분 단위로 입력하면 재시작 없이 바로 적용됩니다. [지금 실행] 버튼도 둡니다. |
| F6 | 실행 기록 | 실행마다 시각, 결과, 매칭 건수, 추가 건수, 로그 원문을 남깁니다. 다운로드 이력도 함께 보여줍니다. |
| F7 | 사이트 관리 | 사이트별 URL, 게시판 경로, 켜기/끄기, 마지막 성공 시각을 관리합니다. 도메인 번호가 바뀌면 +1부터 +5까지 자동 탐색해서 갱신합니다. |
| F8 | Doctor | 사이트 옆의 [doctor] 버튼을 누르면 Claude가 진단합니다. 사이트 상태와 원인, 근거, 수정 제안을 리포트로 보여줍니다. |

## 5. Doctor 상세

**판정 종류**

| 판정 | 의미 |
|---|---|
| `ok` | 정상 |
| `domain_moved` | 도메인 이전 |
| `blocked` | 차단 |
| `site_down` | 사이트 다운 |
| `cloudflare` | Cloudflare 인증 필요 |
| `parser_broken` | 사이트는 정상인데 우리 파서가 실패 |

**진단 도구**: 직접 만든 도구 4개만 Claude에게 줍니다(`create_sdk_mcp_server` + `@tool`). Claude Code에 내장된 WebFetch, Bash 등은 막습니다. 내장 도구는 일반 HTTP 클라이언트를 써서 SNI 차단에 걸리고, 그러면 사이트가 죽었다고 잘못 판정하기 때문입니다.

| 도구 | 하는 일 |
|---|---|
| `dns_tls_check(host)` | DNS 조회, TLS 연결, 가짜 SNI 비교 → 도메인 소멸, 차단, 다운 구분 |
| `browse(url)` | Chromium으로 접속해서 상태 코드, 리다이렉트, 제목, 축약 HTML, CF 챌린지 여부 확인 |
| `run_parser(site)` | 우리 크롤러 파서를 그대로 실행 → 게시글 수, 매칭 예시, magnet 추출 결과 |
| `probe_domains(site)` | 도메인 숫자 +1부터 +5까지 탐색 |

**모델**: 기본은 Sonnet(최신)이고, 화면에서 Opus로 바꿀 수 있습니다. 버전 대신 별칭(`sonnet` / `opus`)으로 지정해서 항상 최신을 씁니다.

**안전장치**
- 실행당 최대 15턴, 비용 상한 $1을 둡니다.
- 읽기 전용 도구만 줍니다.
- 수정 제안은 사용자가 [적용] 버튼으로 반영합니다. 사이트 HTML을 지시가 아닌 데이터로 취급하기 위해서입니다.

**출력**: JSON 스키마(`verdict`, `summary`, `evidence[]`, `suggested_fix{url, boards}`)로 받습니다. 진행 상황은 화면에서 실시간으로 보여주고, 리포트와 실제 비용을 저장합니다.

## 6. 화면

| 화면 | 구성 |
|---|---|
| 대시보드 `/` | 다음 실행 시각, 주기 변경, [지금 실행], 최근 실행과 다운로드 |
| 프로그램 `/programs` | 등록 폼(이름 + 해상도 선택), 목록, 켜기/끄기, 삭제 |
| 사이트 `/sites` | 사이트 목록, 상태, [doctor](모델 선택), 최근 진단 판정 |
| 실행 상세 `/runs/{id}` | 로그 원문 |
| 진단 리포트 `/doctor/{id}` | 판정, 요약, 근거, 수정 제안, [적용], 비용 |

구현은 FastAPI + Jinja2 서버 렌더링으로 하고, 상태 갱신이 필요한 곳(Doctor 진행 상황)만 htmx를 씁니다.

## 7. 데이터

SQLite(stdlib `sqlite3`, ORM 없음)에 테이블 6개를 둡니다.

| 테이블 | 컬럼 |
|---|---|
| `programs` | id, name, resolution (`720p` / `1080p` / `any`), enabled |
| `sites` | id, name, url, boards, enabled, last_ok_at |
| `settings` | key, value (`interval_min`, `doctor_model` 등) |
| `runs` | id, started, finished, status, matched, added, log |
| `downloads` | info_hash (PK), program_id, episode, title, site, added_at. `UNIQUE(program_id, episode)` |
| `doctor_reports` | id, site_id, started, status, model, verdict, report_json, cost_usd |

비밀값(Claude 토큰, Transmission 계정)은 `.env`에만 둡니다. `.env`는 이미 준비되어 있고(권한 600) git 추적에서 제외되어 있습니다.

## 8. 초기 데이터

**사이트**

| 사이트 | URL | 게시판 | 상태 |
|---|---|---|---|
| 토렌트썸 | https://torrentsome268.com | `/v-4-16` (예능) 외 | 켬 |
| 토렌트좋다 | https://torrentzota206.com | `/t/4/16.html` (예능) 외 | 켬 |
| 토렌트티티 | https://torrenttt253.top | `/c/4` (영상·음악) | 켬 |
| 토렌트알지 | https://torrentrj274.com | `/v-4-16` | 끔 (예비) |
| 토렌트밤 | https://torrentbam252.top | `/c/4` | 끔 (예비) |

드라마와 시사 게시판 경로는 구현할 때 확정합니다.

**프로그램**: Pi의 기존 규칙 17개를 가져옵니다. 추천 프로그램인 놀면 뭐하니와 라디오스타는 켠 상태로 둡니다.

라디오스타, 돌싱포맨, PD 수첩(720p), 나 혼자 산다, 미운 우리 새끼, SBS 스페셜(720p), 그것이 알고 싶다, 금쪽 같은(720p), 놀면 뭐하니, 나는 솔로, 전지적, 유 퀴즈, 알쓸인잡, 지구오락실, 태어난, 애프터시그널, 사랑은 계속된다

- 기존 규칙의 릴리즈 그룹 필터(NEXT)는 없앱니다. 같은 회차가 다른 릴리즈로 다시 받아지는 것은 F3의 회차 중복 방지로 막습니다.
- **미정**: 현재 방영하지 않는 프로그램을 꺼진 상태로 가져올지 정해야 합니다.

## 9. 배포와 운영

- 배포는 `.env`를 준비한 뒤 `docker compose up -d` 한 줄입니다. OrbStack이 실행되면 컨테이너도 자동으로 시작됩니다(`restart: unless-stopped`).
- 베이스 이미지는 `mcr.microsoft.com/playwright/python:v1.48.0-noble`입니다. 의존성은 uv로 관리합니다(`pyproject.toml`, `uv.lock`).
- Mac이 잠자는 동안에는 크롤링하지 않습니다. 깨어나면 다음 주기에 바로 실행합니다.
- 웹 UI는 인증이 없으므로 이 Mac(127.0.0.1:8080)에서만 열립니다.

## 10. 범위 밖 (v2에서 하지 않는 것)

- 사용자 인증과 외부 노출
- 알림
- 페이지네이션 (첫 페이지와 DB 중복 방지로 충분)
- 사이트별 전용 파서
- Doctor의 자동 수정
- Pi에서의 실행
- Cloudflare 사람 인증 우회

## 11. 위험 요소

| 위험 | 대응 |
|---|---|
| 사이트 도메인이 자주 바뀜 | 자동 탐색으로 처리하고, 실패하면 Doctor로 진단 |
| 도메인별 첫 접속이 간헐적으로 실패 | 재시도 2회 |
| ISP가 ECH까지 차단할 가능성 | 그때는 VPN이나 프록시 같은 다른 접속 경로가 필요합니다. 현재는 대응 범위 밖입니다 |
| OAuth 토큰 사용 | 본인이 개인적으로 쓰는 범위로 한정합니다. 다른 사람에게 서비스로 제공하면 정책상 API 키가 필요합니다 |

## 12. 구현 단계

| # | 작업 | 확인 방법 |
|---|---|---|
| 1 | Docker 골격 (일부 완료) | 컨테이너에서 3개 사이트 접속, Agent SDK 동작 (완료) |
| 2 | 크롤러와 테스트 | 테스트 통과, dry-run 매칭 결과 확인 |
| 3 | DB, 스케줄러, RPC | 1건 실제 추가 후 Pi Transmission에서 확인, 주기 변경 즉시 반영 |
| 4 | 웹 화면 | 브라우저에서 등록 → 실행 → 기록 확인 |
| 5 | Doctor | 정상 사이트는 `ok`, 막힌 사이트(torrenttop)는 `blocked`, 파서를 일부러 망가뜨리면 `parser_broken` |
| 6 | 초기 데이터 이전과 옛 코드 정리 | `/programs`에 17개 표시, README 갱신 |

## 부록 A. 사이트 점검 결과 (2026-10-18)

| 사이트 | 브라우저 | 스크립트 | 구조 | magnet | 비고 |
|---|---|---|---|---|---|
| 토렌트썸 268 | ✅ | ✅ 720p 에피소드 84건 | 엔진 A `/v-4-16` → `/v/{id}` | 상세 HTML에 있음 | 선정 |
| 토렌트알지 274 | ✅ | ✅ 64건 | 엔진 A (썸과 같은 엔진) | 있음 | 예비 |
| 토렌트좋다 206 | ✅ | ✅ 72건 | 엔진 A 변형 `/t/4/16.html` → `/torrent/{id}.html` | 있음 | 선정 |
| 토렌트티티 253 | ✅ | ✅ 70건 | 엔진 B `/c/4` → `/t/{slug}.html` | 있음, `btih:`가 빠진 형식 | 선정, 정규화 필요 |
| 토렌트밤 252 | ✅ | ✅ 54건 | 엔진 B (티티와 같은 엔진) | 위와 같음 | 예비 |
| 토렌트봇 264 | ✅ (CF 자동 통과) | ❌ headless는 CF 403 | `/topic/{id}` | 있음 | 제외 |
| 토렌트씨 359 | ❌ Turnstile 사람 인증 | ❌ | | | 제외 |
| 토렌트쓱 8 | ✅ | — | | | 로그인 필요, 제외 |
| 토렌트팁 248 | ❌ 에러 페이지 | ❌ | | | 제외 |
| 토렌트탑 226 | ❌ "법적 사유로 이용 불가" | ❌ | | | 제외 |
| 토렌트와이 197 | ❌ "법적 사유로 이용 불가" | ❌ | | | 제외 |

## 부록 B. Pi 환경 (참고)

- Raspberry Pi 4 Model B 2GB, Raspbian 10 Buster armv7l, Python 3.7.3, Chromium 92(ECH 없음), Kodi 실행 중
- Transmission 2.94, RPC 포트 59090, 다운로드 경로 `/home/pi/S_Samba/X_Torrent/temp_bucket`
- 기존 크롤러의 cron 작업은 2026-10-18에 주석 처리했습니다(백업: `~/crontab.backup.20261018`).
