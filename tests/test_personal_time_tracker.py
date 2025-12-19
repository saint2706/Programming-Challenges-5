import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Practical.personal_time_tracker.logic import TimeTracker
from Practical.personal_time_tracker.storage import SessionStore


def run_cli(tmp_path, *args):
    env = os.environ.copy()
    env["PTT_DB_PATH"] = str(tmp_path / "sessions.json")
    # Run as a module to support relative imports
    result = subprocess.run(
        [sys.executable, "-m", "Practical.personal_time_tracker", *args],
        capture_output=True,
        text=True,
        env=env,
        check=True,
        cwd=str(ROOT),
    )
    return result.stdout.strip()


def test_storage_initialization(tmp_path):
    target = tmp_path / "sessions.json"
    store = SessionStore(path=target)
    assert target.exists()
    assert store.all_sessions() == []


def test_time_tracker_start_stop(tmp_path):
    store = SessionStore(path=tmp_path / "sessions.json")
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)

    def fake_now():
        nonlocal now
        current = now
        now = now + timedelta(hours=1)
        return current

    tracker = TimeTracker(store=store, now_func=fake_now)
    tracker.start_session("coding", notes="Feature")
    tracker.stop_session()
    sessions = tracker.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["category"] == "coding"
    report = tracker.report()
    assert list(report.values())[0] == timedelta(hours=1)


def test_cli_workflow(tmp_path):
    out = run_cli(tmp_path, "start", "--category", "reading", "--notes", "Book")
    assert "Started session" in out
    out = run_cli(tmp_path, "stop")
    assert "Stopped session" in out
    out = run_cli(tmp_path, "list")
    assert "reading" in out
    out = run_cli(tmp_path, "report")
    assert "Report" in out
