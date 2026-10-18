from datetime import datetime

from app.views import ago, dt, dur

NOW = datetime(2026, 10, 18, 20, 0, 0)


def test_dt():
    assert dt(None) == "-"
    assert ">19:23</time>" in dt("2026-10-18T19:23:10", NOW)
    assert 'datetime="2026-10-18T19:23:10"' in dt("2026-10-18T19:23:10", NOW)
    assert ">10-17 09:05<" in dt(datetime(2026, 10, 17, 9, 5), NOW)
    assert ">2025-01-02 03:04<" in dt("2025-01-02T03:04:00", NOW)


def test_ago():
    assert ago(None) == "-"
    assert ago("2026-10-18T19:59:30", NOW) == "방금"
    assert ago("2026-10-18T19:23:00", NOW) == "37분 전"
    assert ago(datetime(2026, 10, 18, 22, 30), NOW) == "2시간 후"
    assert ago("2026-10-15T20:00:00", NOW) == "3일 전"


def test_dur():
    assert dur("2026-10-18T19:23:10", "2026-10-18T19:35:40") == "12분 30초"
    assert dur("2026-10-18T19:23:10", "2026-10-18T19:23:55") == "45초"
    assert dur("2026-10-18T19:23:10", None) == "실행 중"
