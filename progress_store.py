"""
Session State & Progress Storage — Fitness Buddy
Manages all in-session state and local progress persistence.
"""

import json
import os
import hashlib
from datetime import datetime, date
from typing import Dict, List, Any, Optional


PROGRESS_FILE = "fitness_buddy_progress.json"


def _load_progress() -> Dict:
    """Load progress data from local JSON file."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return _default_progress()


def _save_progress(data: Dict):
    """Save progress data to local JSON file."""
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        pass  # Graceful degradation if file write fails


def _default_progress() -> Dict:
    return {
        "weekly_active_days": 0,
        "completed_workouts": 0,
        "total_active_minutes": 0,
        "habit_streak": 0,
        "habit_level": 1,
        "habit_days_this_level": 0,
        "energy_readings": [],
        "energy_trend": "stable",
        "current_difficulty": "beginner",
        "achievements": [],
        "workout_log": [],
        "last_checkin_date": None,
        "weekly_reset_date": str(date.today()),
        "readiness_scores": [],
        "session_count": 0,
    }


def get_progress() -> Dict:
    return _load_progress()


def record_workout(duration_minutes: int, difficulty: str, workout_type: str):
    """Record a completed workout session."""
    data = _load_progress()
    today = str(date.today())

    # Weekly reset check
    reset_date = data.get("weekly_reset_date", today)
    days_since_reset = (date.today() - date.fromisoformat(reset_date)).days
    if days_since_reset >= 7:
        data["weekly_active_days"] = 0
        data["weekly_reset_date"] = today

    # Record workout
    data["completed_workouts"] += 1
    data["total_active_minutes"] += duration_minutes

    # Active days (no duplicates per day)
    log = data.get("workout_log", [])
    today_logged = any(entry.get("date") == today for entry in log)
    if not today_logged:
        data["weekly_active_days"] = min(data["weekly_active_days"] + 1, 7)

    log.append({
        "date": today,
        "duration": duration_minutes,
        "difficulty": difficulty,
        "type": workout_type,
    })
    data["workout_log"] = log[-50:]  # Keep last 50 entries

    # Difficulty progression
    if data["completed_workouts"] >= 20 and data["current_difficulty"] == "beginner":
        data["current_difficulty"] = "intermediate"
        _add_achievement(data, "🌟 Leveled up to Intermediate!")
    elif data["completed_workouts"] >= 50 and data["current_difficulty"] == "intermediate":
        data["current_difficulty"] = "advanced"
        _add_achievement(data, "🏆 Reached Advanced level!")

    # Achievements
    if data["completed_workouts"] == 1:
        _add_achievement(data, "🎉 First workout completed!")
    if data["completed_workouts"] == 10:
        _add_achievement(data, "💪 10 workouts done!")
    if data["total_active_minutes"] >= 300:
        if "300 active minutes" not in str(data["achievements"]):
            _add_achievement(data, "⏱️ 300+ active minutes achieved!")

    _save_progress(data)
    return data


def record_checkin(energy: str, readiness_score: int):
    """Record daily check-in data."""
    data = _load_progress()
    today = str(date.today())

    # Habit streak
    last_checkin = data.get("last_checkin_date")
    if last_checkin:
        days_diff = (date.today() - date.fromisoformat(last_checkin)).days
        if days_diff == 1:
            data["habit_streak"] += 1
        elif days_diff > 1:
            data["habit_streak"] = 1  # Reset streak
    else:
        data["habit_streak"] = 1

    data["last_checkin_date"] = today

    # Energy trend
    readings = data.get("energy_readings", [])
    energy_val = {"low": 1, "medium": 2, "high": 3}.get(energy, 2)
    readings.append(energy_val)
    readings = readings[-14:]  # Keep last 2 weeks
    data["energy_readings"] = readings

    if len(readings) >= 3:
        recent_avg = sum(readings[-3:]) / 3
        older_avg = sum(readings[:-3]) / max(len(readings) - 3, 1)
        if recent_avg > older_avg + 0.3:
            data["energy_trend"] = "improving"
        elif recent_avg < older_avg - 0.3:
            data["energy_trend"] = "declining"
        else:
            data["energy_trend"] = "stable"

    # Readiness scores
    scores = data.get("readiness_scores", [])
    scores.append({"date": today, "score": readiness_score})
    data["readiness_scores"] = scores[-30:]

    # Streak achievements
    if data["habit_streak"] == 7:
        _add_achievement(data, "🔥 7-day streak! One full week!")
    if data["habit_streak"] == 30:
        _add_achievement(data, "🌙 30-day streak! A full month!")

    data["session_count"] = data.get("session_count", 0) + 1
    _save_progress(data)
    return data


def advance_habit_level(data: Optional[Dict] = None) -> Dict:
    """Check if user should advance to next habit level."""
    if data is None:
        data = _load_progress()

    from features import get_current_habit
    current_level = data.get("habit_level", 1)
    days_this_level = data.get("habit_days_this_level", 0)
    habit = get_current_habit(current_level)
    consistency_needed = habit["consistency_needed"]

    if days_this_level >= consistency_needed and current_level < 5:
        data["habit_level"] = current_level + 1
        data["habit_days_this_level"] = 0
        new_habit = get_current_habit(data["habit_level"])
        _add_achievement(data, f"⬆️ Habit Level {data['habit_level']}: {new_habit['habit']}!")
        _save_progress(data)

    return data


def increment_habit_day():
    """Mark today's habit as completed."""
    data = _load_progress()
    data["habit_days_this_level"] = data.get("habit_days_this_level", 0) + 1
    _save_progress(data)
    advance_habit_level(data)
    return _load_progress()


def _add_achievement(data: Dict, achievement: str):
    """Add a unique achievement to the list."""
    achievements = data.get("achievements", [])
    if achievement not in achievements:
        achievements.append(achievement)
        data["achievements"] = achievements[-20:]  # Keep last 20
