#!/bin/bash
# claude 실행 래퍼. -w/--worktree 로 git worktree 격리 세션을 켤 수 있다.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./run-claude.sh [-w|--worktree [name]] [-- <extra claude args>]

  -w, --worktree [name]   세션용 git worktree 생성(이름 선택). claude 의 --worktree 로 전달.
      --tmux              worktree 를 tmux 세션으로(--worktree 필요). claude 의 --tmux 로 전달.
  -y, --yolo              모든 권한 확인을 건너뛴다. claude 의 --dangerously-skip-permissions 로 전달.
  -h, --help              이 도움말.

이외 인자는 그대로 claude 로 전달된다.
EOF
}

# 세션 표시 이름은 저장소 디렉터리 이름을 쓴다. 특정 프로젝트 이름을 박지 않는다.
claude_args=(--verbose -n "$(basename "$PWD")")

while [[ $# -gt 0 ]]; do
  case "$1" in
    -w | --worktree)
      # 다음 인자가 옵션(-)이 아니면 worktree 이름으로 소비
      if [[ ${2-} && ${2:0:1} != "-" ]]; then
        claude_args+=(--worktree "$2")
        shift 2
      else
        claude_args+=(--worktree)
        shift
      fi
      ;;
    --tmux)
      claude_args+=(--tmux)
      shift
      ;;
    -y | --yolo)
      claude_args+=(--dangerously-skip-permissions)
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    --)
      shift
      claude_args+=("$@")
      break
      ;;
    *)
      claude_args+=("$1")
      shift
      ;;
  esac
done

exec claude "${claude_args[@]}"
