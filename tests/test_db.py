import sqlite3

import pytest

from app import db

HASH = "4e4d86cbee91db107def6d3fd24271afd28130e2"


def test_seed_and_rules(tmp_path):
    path = tmp_path / "app.db"
    db.connect(path).close()
    conn = db.connect(path)
    assert len(db.list_programs(conn)) == 17 and len(db.list_sites(conn)) == 5
    assert {p["name"] for p in db.list_programs(conn, enabled_only=True)} == {"놀면 뭐하니", "라디오스타"}
    assert len(db.list_sites(conn, enabled_only=True)) == 3
    assert db.get_setting(conn, "interval_min") == "60" and db.get_setting(conn, "doctor_model") == "sonnet"
    assert db.get_site(conn, 1)["boards"] == ["/v-4-16", "/v-2-13", "/v-4-17"]

    p = db.list_programs(conn, enabled_only=True)[0]["id"]
    assert db.add_download(conn, HASH, p, "E348.261017", "t", "s")
    assert not db.add_download(conn, HASH, p, "E999", "t", "s")
    assert not db.add_download(conn, "0" * 40, p, "E348.261017", "t", "s")
    assert db.episode_exists(conn, p, "E348.261017") and db.download_exists(conn, HASH)
    assert db.add_download(conn, "1" * 40, p, None, "t", "s")
    assert db.add_download(conn, "2" * 40, p, None, "t", "s")
    assert db.list_downloads(conn)[0]["program_name"]


def test_program_validation(tmp_path):
    conn = db.connect(tmp_path / "app.db")
    for name, res in [("", []), ("x", ["480p"]), ("라디오스타", [])]:
        with pytest.raises(ValueError):
            db.add_program(conn, name, res)
    pid = db.add_program(conn, "x", ["1080p", "720p"])
    assert db.list_programs(conn)[-1]["resolution"] == "720p,1080p"
    db.set_program_resolution(conn, pid, [])
    assert db.list_programs(conn)[-1]["resolution"] == "any"
    with pytest.raises(ValueError):
        db.set_program_resolution(conn, pid, ["480p"])


def test_clean_resolution():
    assert db.clean_resolution([]) == "any"
    assert db.clean_resolution(["any"]) == "any"
    assert db.clean_resolution(["", " "]) == "any"
    assert db.clean_resolution(["1080p", "720p", "720p"]) == "720p,1080p"
    with pytest.raises(ValueError):
        db.clean_resolution(["480p"])


def test_migrate_old_programs_check(tmp_path):
    path = tmp_path / "app.db"
    old = sqlite3.connect(path)
    old.executescript(db.DDL.replace("CHECK (resolution <> '')", "CHECK (resolution IN ('720p','1080p','any'))"))
    old.execute("INSERT INTO programs(id, name, resolution) VALUES (7, '놀면', '720p')")
    old.execute("INSERT INTO downloads VALUES (?, 7, 'E1', 't', 's', '2026-10-18T00:00:00')", (HASH,))
    old.commit()
    old.close()
    conn = db.connect(path)
    db.set_program_resolution(conn, 7, ["720p", "1080p"])
    assert db.list_programs(conn)[0]["resolution"] == "720p,1080p"
    assert db.list_downloads(conn)[0]["program_id"] == 7
    conn.close()
    db.connect(path).close()  # second connect: no rebuild


def test_migrate_adds_site_pages(tmp_path):
    path = tmp_path / "app.db"
    old = sqlite3.connect(path)
    old.executescript(db.DDL.replace(",\n  " + db.PAGES_COL, ""))
    old.execute("INSERT INTO sites(name, url) VALUES ('a', 'https://a.com')")
    old.commit()
    old.close()
    conn = db.connect(path)
    assert db.get_site(conn, 1)["pages"] == 3
    db.update_site(conn, 1, pages=5)
    assert db.get_site(conn, 1)["pages"] == 5
    with pytest.raises(sqlite3.IntegrityError):
        db.update_site(conn, 1, pages=11)


def test_stale_marking_and_progress(tmp_path):
    path = tmp_path / "app.db"
    conn = db.connect(path)
    rid = db.create_run(conn)
    did = db.create_doctor_report(conn, 1, "sonnet")
    db.append_doctor_progress(conn, did, "one")
    db.append_doctor_progress(conn, did, "two")
    assert db.get_doctor_report(conn, did)["progress"].splitlines() == ["one", "two"]
    conn.close()
    conn = db.connect(path)
    assert db.get_run(conn, rid)["status"] == "error"
    assert db.get_doctor_report(conn, did)["status"] == "error"
    assert db.latest_doctor_report_per_site(conn)[1]["id"] == did


def test_clean_site_fields():
    assert db.clean_site_fields(" https://x.com/ ", ["/a", "", " /b "]) == ("https://x.com", ["/a", "/b"])
    for url, boards in [("https://x.com?", ["/a"]), ("https://x.com", []), ("https://x.com", ["", " "]),
                        ("https://x.com", ["/a\n/b"]), ("https://x.com", ["a"]), ("ftp://x.com", ["/a"])]:
        with pytest.raises(ValueError):
            db.clean_site_fields(url, boards)
