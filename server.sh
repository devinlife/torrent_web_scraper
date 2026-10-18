#!/bin/bash
# dev/prod 서버 제어 래퍼. docker compose 프로젝트를 환경별로 나눠 실행한다.
set -euo pipefail
cd "$(dirname "$0")"

usage() {
  cat <<'USAGE'
Usage: ./server.sh <dev|prod> <command>

  up        이미지를 빌드하고 백그라운드로 띄운다.
  down      컨테이너를 내린다. 데이터(./data/<env>)는 남는다.
  restart   컨테이너를 재시작한다(이미지 재빌드 없음).
  reset     내리고 DB를 지운 뒤 다시 띄운다. 시드 데이터로 새로 시작한다.
  logs      로그를 따라 본다.
  ps        컨테이너 상태를 본다.
  dry-run   크롤링을 한 번 실행하고 로그를 출력한다. Transmission 추가와 URL 변경은 하지 않는다.

  dev   http://127.0.0.1:8081  ./data/dev   모든 실행이 dry-run, ./app 저장 시 자동 재시작
  prod  http://127.0.0.1:8080  ./data/prod  Transmission에 실제로 추가
USAGE
}

case "${1-}" in
  dev) file=compose.dev.yaml url=http://127.0.0.1:8081 ;;
  prod) file=compose.yaml url=http://127.0.0.1:8080 ;;
  -h | --help) usage; exit 0 ;;
  *) usage >&2; exit 1 ;;
esac
env=$1
data=data/$env
dc() { docker compose -f "$file" "$@"; }

case "${2-}" in
  up)
    mkdir -p "$data"
    dc up -d --build
    echo "$env: $url"
    ;;
  down) dc down ;;
  restart) dc restart ;;
  reset)
    if [[ $env == prod ]]; then
      # 다운로드 기록이 사라지면 첫 페이지에 남은 회차를 다시 추가하려 한다.
      read -r -p "prod DB($data/app.db)와 다운로드 기록을 지웁니다. 계속하려면 prod를 입력: " answer
      [[ $answer == prod ]] || { echo "취소했다." >&2; exit 1; }
    fi
    dc down
    rm -f "$data"/app.db "$data"/app.db-wal "$data"/app.db-shm
    mkdir -p "$data"
    dc up -d --build
    echo "$env: $url (DB 초기화)"
    ;;
  logs) dc logs -f ;;
  ps) dc ps ;;
  dry-run) mkdir -p "$data"; dc run --rm scraper python -m app.scheduler --dry-run ;;
  *) usage >&2; exit 1 ;;
esac
