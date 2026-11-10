"""
Feature Modules — Fitness Buddy
Implements all 8 feature areas (A–H) with prompt builders for IBM Granite.
"""

from typing import Dict, List, Optional, Any


# ─────────────────────────────────────────────────────────────
# COACH PERSONALITY SYSTEM PROMPTS (Feature F)
# ─────────────────────────────────────────────────────────────

COACH_PERSONAS = {
    "Gentle Friend": (
        "You are a warm, supportive, and non-judgmental fitness friend. "
        "Use encouraging language, celebrate small wins, and never make the user feel guilty. "
        "Be empathetic and understanding. Always prioritize the user's comfort and wellbeing."
    ),
    "Energetic Coach": (
        "You are an enthusiastic, high-energy fitness coach! "
        "Use motivating, challenge-oriented language. Add energy words like 'Let's GO!', 'You've got this!'. "
        "Push the user to do their best while keeping it fun and exciting."
    ),
    "Calm Guide": (
        "You are a calm, mindful fitness guide. "
        "Be concise, clear, and peaceful in your guidance. Focus on mindfulness, breathing, and sustainable habits. "
        "Use a gentle, measured tone. Quality over quantity."
    ),
    "Accountability Partner": (
        "You are a direct, no-nonsense accountability partner. "
        "Be honest, respectful, and consistent. Track commitments, call out excuses kindly but firmly, "
        "and keep the user focused on their goals. You believe in the user's ability to succeed."
    ),
}

BASE_SYSTEM_PROMPT = """You are Fitness Buddy, an AI-powered health and fitness coach.
You provide safe, practical, and personalized fitness guidance.

IMPORTANT RULES:
- Never provide medical diagnoses or prescriptions.
- Always recommend consulting a doctor for medical conditions.
- Suggest practical, accessible exercises and meals (especially Indian household options).
- Be inclusive and respectful of all body types, ages, and fitness levels.
- Keep recommendations realistic and achievable.
- Format your response clearly with headers and bullet points.
- Keep responses concise and actionable (max 300 words unless asked for more).
"""


def build_system_prompt(coach_style: str = "Gentle Friend") -> str:
    """Build the complete system prompt with chosen coach persona."""
    persona = COACH_PERSONAS.get(coach_style, COACH_PERSONAS["Gentle Friend"])
    return f"{BASE_SYSTEM_PROMPT}\nCOACH STYLE:\n{persona}"


# ─────────────────────────────────────────────────────────────
# A. ADAPTIVE DAILY CHECK-IN
# ─────────────────────────────────────────────────────────────

def build_checkin_prompt(checkin_data: Dict) -> str:
    """Build prompt for adaptive daily check-in workout plan."""
    return f"""Based on the user's daily check-in, generate a personalized fitness plan for today.

USER'S CHECK-IN:
- Available time: {checkin_data.get('time', '20')} minutes
- Energy level: {checkin_data.get('energy', 'medium')}
- Current mood: {checkin_data.get('mood', 'neutral')}
- Workout location: {checkin_data.get('location', 'home')}
- Available equipment: {checkin_data.get('equipment', 'none')}
- Experience level: {checkin_data.get('experience', 'beginner')}
- Areas of pain/discomfort: {checkin_data.get('pain_areas', 'none')}
- Preferred intensity: {checkin_data.get('intensity', 'moderate')}

Generate a workout plan that:
1. Fits exactly within the available time
2. Matches the energy level (low energy = gentler, high energy = more intense)
3. Avoids exercises that stress the mentioned pain areas
4. Uses only the available equipment
5. Suits the experience level

Format as:
**Today's Plan** (time)
**Warm-Up** (X min): exercises
**Main Workout** (X min): exercises with sets/reps
**Cool Down** (X min): stretches
**Tip for today:** one motivational line
"""


# ─────────────────────────────────────────────────────────────
# B. MINIMUM VIABLE WORKOUT
# ─────────────────────────────────────────────────────────────

MVW_TYPES = {
    "3-minute mobility": "A gentle 3-minute full-body mobility routine",
    "5-minute walk": "A 5-minute walking challenge with pace variations",
    "chair-based": "A seated chair-based exercise routine",
    "breathing & stretching": "A calming breathing and light stretching session",
    "one-round bodyweight": "A single round of simple bodyweight exercises",
}


def build_mvw_prompt(mvw_type: str = "3-minute mobility", reason: str = "tired") -> str:
    """Build prompt for Minimum Viable Workout."""
    description = MVW_TYPES.get(mvw_type, MVW_TYPES["3-minute mobility"])
    return f"""The user is {reason} today but still wants to move their body.
Generate a {description}.

Requirements:
- Maximum 5 minutes total
- Very low intensity — anyone can do this
- No equipment needed
- Clear step-by-step instructions
- End with an encouraging note: "Even this counts as a win!"

Format:
**{mvw_type.title()} Routine**
Duration: X minutes
Step 1: ...
Step 2: ...
...
✅ Done! [encouraging message]
"""


# ─────────────────────────────────────────────────────────────
# C. PLAN B MODIFICATIONS
# ─────────────────────────────────────────────────────────────

PLAN_B_MODIFICATIONS = {
    "Make it easier": "Reduce intensity, add rest, use simpler movements",
    "Make it harder": "Increase reps, add resistance, reduce rest time",
    "No-equipment alternative": "Replace all equipment-based exercises with bodyweight versions",
    "Quiet apartment version": "Replace jumping/loud exercises with silent alternatives",
    "Low-impact version": "Remove all high-impact movements, use low-impact substitutes",
    "Shorten to 5 minutes": "Compress the entire workout into the 5 most effective exercises",
}


def build_plan_b_prompt(original_workout: str, modification: str) -> str:
    """Build prompt for Plan B workout modification."""
    mod_description = PLAN_B_MODIFICATIONS.get(modification, modification)
    return f"""Take this workout and apply the following modification: "{modification}"
Modification goal: {mod_description}

ORIGINAL WORKOUT:
{original_workout}

Generate the modified version. Keep the same format as the original.
Label it clearly: **Modified Plan: {modification}**
Explain in one line why each change was made.
"""


# ─────────────────────────────────────────────────────────────
# D. SMART MEAL BUILDER
# ─────────────────────────────────────────────────────────────

def build_meal_prompt(meal_data: Dict) -> str:
    """Build prompt for Smart Meal Builder."""
    ingredients = meal_data.get("ingredients", "rice, dal, vegetables")
    preference = meal_data.get("preference", "vegetarian")
    allergies = meal_data.get("allergies", "none")
    cook_time = meal_data.get("cook_time", "30 minutes")
    budget = meal_data.get("budget", "low")
    meal_type = meal_data.get("meal_type", "lunch")
    regional = meal_data.get("regional", "Indian")

    return f"""Suggest 2-3 practical {meal_type} meal options using the information below.

USER'S PANTRY & PREFERENCES:
- Available ingredients: {ingredients}
- Dietary preference: {preference}
- Allergies: {allergies}
- Cooking time available: {cook_time}
- Budget: {budget}
- Meal type: {meal_type}
- Regional preference: {regional}

Guidelines:
- Prioritize {regional} household staples (dal, roti, rice, vegetables, paneer, eggs, poha, chana, sprouts, curd)
- Keep it practical and affordable
- Include approximate prep time for each meal
- Add one simple nutritional benefit per meal
- Do NOT present as a medical diet or guaranteed weight-loss solution

Format for each meal:
**Meal Name**
⏱️ Time: X minutes
🥘 Ingredients used: ...
📝 Quick instructions: ...
💚 Benefit: ...
"""


# ─────────────────────────────────────────────────────────────
# E. HABIT LADDER
# ─────────────────────────────────────────────────────────────

HABIT_LADDER_STEPS = [
    {
        "level": 1,
        "habit": "Drink one additional glass of water",
        "description": "Add one extra glass of water to your day",
        "consistency_needed": 3,  # days
        "emoji": "💧",
    },
    {
        "level": 2,
        "habit": "Walk for 5 minutes",
        "description": "Take a 5-minute walk once a day",
        "consistency_needed": 5,
        "emoji": "🚶",
    },
    {
        "level": 3,
        "habit": "Short mobility routine",
        "description": "Complete a 3-minute morning mobility routine",
        "consistency_needed": 5,
        "emoji": "🤸",
    },
    {
        "level": 4,
        "habit": "Add a balanced breakfast",
        "description": "Eat a nutritious breakfast every morning",
        "consistency_needed": 7,
        "emoji": "🥗",
    },
    {
        "level": 5,
        "habit": "Follow a structured workout",
        "description": "Complete a full 20+ minute workout session",
        "consistency_needed": 7,
        "emoji": "💪",
    },
]


def get_current_habit(level: int) -> Dict:
    """Get the current habit step for a given level."""
    idx = min(level - 1, len(HABIT_LADDER_STEPS) - 1)
    return HABIT_LADDER_STEPS[idx]


def build_habit_prompt(level: int, days_consistent: int, coach_style: str = "Gentle Friend") -> str:
    """Build prompt for habit coaching."""
    current_habit = get_current_habit(level)
    next_habit = get_current_habit(min(level + 1, 5))
    days_needed = current_habit["consistency_needed"]
    days_remaining = max(0, days_needed - days_consistent)

    return f"""The user is working on their Habit Ladder — a progressive habit-building system.

CURRENT STATUS:
- Current level: {level}/5
- Current habit: {current_habit['habit']}
- Days consistent: {days_consistent}/{days_needed}
- Days until next level: {days_remaining}
- Next habit to unlock: {next_habit['habit']}

Generate a brief habit coaching message that:
1. Celebrates their current progress
2. Explains why consistency at this level matters
3. Gives one practical tip for today's habit
4. Teases what's coming at the next level (if applicable)
5. Is warm and encouraging

Keep it under 150 words. Make it feel personal and achievable.
"""


# ─────────────────────────────────────────────────────────────
# G. FITNESS READINESS SCORE
# ─────────────────────────────────────────────────────────────

def calculate_readiness_score(checkin: Dict) -> Dict:
    """
    Calculate a daily fitness readiness score (0–100).
    Based on user self-reported metrics — NOT a medical assessment.
    """
    score_components = {}

    # Energy level (0-25 points)
    energy_map = {"low": 8, "medium": 17, "high": 25}
    score_components["energy"] = energy_map.get(checkin.get("energy", "medium"), 17)

    # Sleep quality (0-20 points)
    sleep_hours = float(checkin.get("sleep_hours", 7))
    if sleep_hours >= 8:
        score_components["sleep"] = 20
    elif sleep_hours >= 7:
        score_components["sleep"] = 16
    elif sleep_hours >= 6:
        score_components["sleep"] = 10
    else:
        score_components["sleep"] = 4

    # Mood (0-15 points)
    mood_map = {
        "great": 15, "good": 12, "neutral": 8,
        "tired": 5, "stressed": 5, "anxious": 4, "sad": 3,
    }
    score_components["mood"] = mood_map.get(checkin.get("mood", "neutral").lower(), 8)

    # Soreness (0-15 points) — inverted
    soreness_map = {"none": 15, "mild": 11, "moderate": 7, "severe": 2}
    score_components["soreness"] = soreness_map.get(checkin.get("soreness", "none").lower(), 11)

    # Available time (0-15 points)
    time_min = int(str(checkin.get("time", "20")).split()[0])
    if time_min >= 30:
        score_components["time"] = 15
    elif time_min >= 20:
        score_components["time"] = 12
    elif time_min >= 10:
        score_components["time"] = 8
    else:
        score_components["time"] = 4

    # Recent activity (0-10 points)
    rest_days = int(checkin.get("rest_days_since_last_workout", 1))
    if rest_days == 1:
        score_components["recovery"] = 10
    elif rest_days == 0:
        score_components["recovery"] = 6  # worked out yesterday, may need rest
    elif rest_days <= 3:
        score_components["recovery"] = 8
    else:
        score_components["recovery"] = 4

    total = sum(score_components.values())

    # Determine recommended intensity
    if total >= 75:
        intensity = "High"
        recommendation = "You're ready for a full, challenging workout today! 💪"
    elif total >= 55:
        intensity = "Moderate"
        recommendation = "A moderate workout suits you well today. Listen to your body!"
    elif total >= 35:
        intensity = "Light"
        recommendation = "A gentle, light session is ideal. Focus on movement and recovery."
    else:
        intensity = "Minimal"
        recommendation = "Rest or a very gentle stretch/walk is best today. Recovery is progress too!"

    return {
        "total": total,
        "max": 100,
        "percentage": total,
        "components": score_components,
        "recommended_intensity": intensity,
        "recommendation": recommendation,
        "disclaimer": "⚠️ This score is for general wellness guidance only, not medical assessment.",
    }


# ─────────────────────────────────────────────────────────────
# H. PROGRESS TRACKING (Beyond Weight)
# ─────────────────────────────────────────────────────────────

def build_progress_summary(progress_data: Dict) -> str:
    """Build a formatted progress summary."""
    weekly_days = progress_data.get("weekly_active_days", 0)
    completed_workouts = progress_data.get("completed_workouts", 0)
    total_minutes = progress_data.get("total_active_minutes", 0)
    habit_streak = progress_data.get("habit_streak", 0)
    energy_trend = progress_data.get("energy_trend", "stable")
    current_difficulty = progress_data.get("current_difficulty", "beginner")
    achievements = progress_data.get("achievements", [])

    achievements_str = "\n".join([f"🏆 {a}" for a in achievements]) if achievements else "Keep going to earn your first achievement!"

    return f"""
📊 **Your Progress This Week**

| Metric | Value |
|--------|-------|
| 🗓️ Active Days | {weekly_days}/7 days |
| ✅ Workouts Completed | {completed_workouts} |
| ⏱️ Total Active Time | {total_minutes} minutes |
| 🔥 Habit Streak | {habit_streak} days |
| ⚡ Energy Trend | {energy_trend.title()} |
| 🎯 Current Level | {current_difficulty.title()} |

**Achievements:**
{achievements_str}

*Progress is about consistency, not perfection. Every active day counts!*
"""


def build_motivation_prompt(coach_style: str, user_stats: Dict) -> str:
    """Build a personalized motivation message."""
    days_active = user_stats.get("weekly_active_days", 0)
    streak = user_stats.get("habit_streak", 0)
    last_workout = user_stats.get("last_workout_type", "workout")

    return f"""Generate a personalized motivational message for a fitness app user.

USER STATS:
- Active days this week: {days_active}/7
- Habit streak: {streak} days
- Last activity: {last_workout}

Create a 3-4 sentence motivational message that:
1. Acknowledges their specific progress (use the actual numbers)
2. Encourages them to keep going without guilt if they missed days
3. Sets a positive intention for today
4. Ends with a concrete, small action they can take right now

Keep it personal, warm, and genuine. Avoid clichés.
"""


def get_workout_alternatives(workout_type: str) -> Dict[str, str]:
    """Return Plan B alternatives for any workout."""
    return {
        "Make it easier": f"Reduce reps by 50%, add 30s rest between each exercise, use wall support",
        "Make it harder": f"Add 5 more reps per set, reduce rest time to 20s, add a weighted object",
        "No-equipment alternative": f"Replace all weights with water bottles/books, use bodyweight for resistance",
        "Quiet apartment version": f"Remove all jumping jacks/jumps, replace with march-in-place, slow controlled movements",
        "Low-impact version": f"No jumping, all movements performed standing or seated, step instead of jump",
        "Shorten to 5 minutes": f"Pick top 3 exercises, do 1 set each for 45 seconds with 15s rest",
    }


def get_minimum_viable_workouts() -> List[Dict]:
    """Return the list of Minimum Viable Workout options."""
    return [
        {
            "name": "3-Minute Mobility Routine",
            "time": "3 minutes",
            "description": "Full-body gentle mobility for stiff joints",
            "exercises": [
                "Neck rolls — 5 each direction",
                "Shoulder circles — 10 each arm",
                "Hip circles — 10 each direction",
                "Ankle rotations — 10 each foot",
                "Seated forward bend — 30 seconds",
            ],
        },
        {
            "name": "5-Minute Walking Challenge",
            "time": "5 minutes",
            "description": "Indoor or outdoor walking with pace variations",
            "exercises": [
                "1 min: Slow stroll (warm up)",
                "1 min: Brisk walk / march in place",
                "1 min: Slow stroll (recover)",
                "1 min: Brisk walk / march in place",
                "1 min: Slow cool-down stroll",
            ],
        },
        {
            "name": "Chair-Based Routine",
            "time": "5 minutes",
            "description": "Seated exercises for all mobility levels",
            "exercises": [
                "Seated marching — 20 steps",
                "Chair sit-to-stand — 10 reps",
                "Seated arm raises — 15 reps",
                "Ankle pumps — 20 reps",
                "Seated side bends — 10 each side",
            ],
        },
        {
            "name": "Breathing & Stretching",
            "time": "5 minutes",
            "description": "Calm breathwork and gentle stretching",
            "exercises": [
                "Box breathing: 4s inhale, 4s hold, 4s exhale — 4 rounds",
                "Neck side stretch — 30s each side",
                "Chest opener stretch — 30s",
                "Seated spinal twist — 30s each side",
                "Progressive muscle relaxation — 1 minute",
            ],
        },
        {
            "name": "One-Round Bodyweight",
            "time": "5 minutes",
            "description": "One circuit of simple bodyweight exercises",
            "exercises": [
                "Squats × 10",
                "Push-ups (knee or full) × 8",
                "Glute bridges × 12",
                "Plank hold × 20 seconds",
                "Mountain climbers × 10",
            ],
        },
    ]
