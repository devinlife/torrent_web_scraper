---
name: scraper-verify
description: torrent_web_scraper 리포에서 변경을 마치기 전에 로컬 검증을 돌릴 때 사용한다. 테스트 실행 방법과 통과 기준을 담는다.
---

# scraper-verify

변경을 마쳤다고 보고하기 전에 리포 루트에서 다음을 실행한다.

```sh
uv run pytest
```

- 모든 테스트가 통과해야 완료로 본다. 실패하면 원인을 고치고 다시 돌린다.
- Playwright가 필요한 테스트가 브라우저 미설치로 실패하면 그 사실을 보고하고, 테스트를 지우거나 건너뛰게 고치지 않는다.
