from datetime import datetime, timedelta
from pathlib import Path

import pytest
from Practical.TerminalHabitCoach.database import HabitRepository
from Practical.TerminalHabitCoach.service import TerminalHabitCoach


def test_streaks_increment_and_reset(tmp_path: Path):
    repo = HabitRepository(db_path=tmp_path / "habits.db")
    coach = TerminalHabitCoach(repository=repo)
    coach.add_habit("Meditate", reminder_time="08:00")

    day1 = datetime(2024, 5, 1, 8)
    day2 = day1 + timedelta(days=1)
    day4 = day1 + timedelta(days=3)

    coach.log("Meditate", when=day1.isoformat())
    coach.log("Meditate", when=day2.isoformat())
    coach.log("Meditate", when=day4.isoformat())

    stats = repo.get_habit_stats("Meditate")
    assert stats["current_streak"] == 1
    assert stats["longest_streak"] == 2
    assert stats["total_logs"] == 3


def test_database_persists_habits_and_reminders(tmp_path: Path):
    db_path = tmp_path / "habits.db"
    repo = HabitRepository(db_path=db_path)
    repo.add_habit("Journal", description="Reflect", reminder_time="21:00")
    repo.add_habit("Stretch", description="Mobility", reminder_time="09:00")

    repo.log_habit("Journal")

    stats = repo.get_all_stats()
    assert len(stats) == 2

    reminders = repo.habits_needing_reminder()
    names = {habit.name for habit in reminders}
    assert "Stretch" in names  # never logged so should remind
    assert "Journal" not in names  # already logged today


def test_cli_status_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    repo = HabitRepository(db_path=tmp_path / "habits.db")
    coach = TerminalHabitCoach(repository=repo)
    coach.add_habit("Read", description="Book", reminder_time="20:00")
    coach.log("Read")

    for line in coach.list_status():
        print(line)

    output = capsys.readouterr().out
    assert "Read" in output
    assert "Reminders" not in output  # already logged today
