"""
IBM Granite AI Integration Module
Handles all communication with IBM watsonx.ai Granite models.

Supported models confirmed on this watsonx.ai account:
  ibm/granite-4-h-small          (primary — instruct, latest Granite)
  ibm/granite-3-1-8b-base        (fallback — completion model)
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_ENV_PATH = Path(__file__).parent / ".env"

# ── Confirmed-available IBM Granite models on watsonx.ai Lite tier ────────────
# Use ibm/granite-4-h-small first (instruct model, best for chat).
# ibm/granite-3-1-8b-base is a completion model — we add an instruction prefix
# so it responds helpfully even without a chat fine-tune.
SUPPORTED_GRANITE_MODELS = [
    "ibm/granite-4-h-small",
    "ibm/granite-3-1-8b-base",
]
DEFAULT_MODEL_ID = "ibm/granite-4-h-small"


def _reload_env() -> None:
    """Force-reload .env so edits after server start are picked up instantly."""
    if _ENV_PATH.exists():
        load_dotenv(dotenv_path=_ENV_PATH, override=True)


_reload_env()  # load on import


class GraniteClient:
    """IBM watsonx.ai Granite model client."""

    def __init__(self):
        _reload_env()
        self.max_tokens = int(os.getenv("MAX_TOKENS", "800"))

    # ── Credential check ──────────────────────────────────────────────────────

    def is_configured(self) -> bool:
        """
        Read os.environ live on every call — the sidebar status badge
        reflects .env changes without needing a server restart.
        """
        api_key    = os.getenv("IBM_API_KEY", "").strip()
        project_id = os.getenv("IBM_PROJECT_ID", "").strip()
        bad = {"", "your_ibm_api_key_here", "your_watsonx_project_id_here",
               "none", "null", "undefined"}
        return api_key not in bad and project_id not in bad

    # ── Main generation ───────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a response from IBM Granite.
        - Reloads .env before every call.
        - Tries confirmed-available models in order; falls back to rich
          template responses only when all API calls fail.
        """
        _reload_env()

        if not self.is_configured():
            return self._smart_demo(prompt)

        api_key    = os.getenv("IBM_API_KEY", "").strip()
        project_id = os.getenv("IBM_PROJECT_ID", "").strip()
        url        = os.getenv("IBM_WATSONX_URL",
                               "https://us-south.ml.cloud.ibm.com").strip()
        model_id   = os.getenv("IBM_GRANITE_MODEL_ID", DEFAULT_MODEL_ID).strip()

        tokens     = max_tokens or self.max_tokens

        # Build the formatted prompt. granite-4-h-small uses the chat template;
        # granite-3-1-8b-base uses a plain completion prefix.
        def _build_prompt(mid: str) -> str:
            if "base" in mid:
                # Completion model — prefix with a concise instruction header.
                return (
                    f"### Instruction:\n{system_prompt}\n\n"
                    f"### Input:\n{prompt}\n\n"
                    f"### Response:\n"
                ) if system_prompt else f"### Input:\n{prompt}\n\n### Response:\n"
            else:
                # Instruct / chat model — use standard chat tags.
                sys_block = f"<|system|>\n{system_prompt}\n" if system_prompt else ""
                return f"{sys_block}<|user|>\n{prompt}\n<|assistant|>\n"

        # Try configured model first, then fallback list.
        models_to_try = [model_id] + [m for m in SUPPORTED_GRANITE_MODELS
                                       if m != model_id]

        for attempt_model in models_to_try:
            try:
                from ibm_watsonx_ai.foundation_models import ModelInference
                from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GP
                from ibm_watsonx_ai import Credentials

                creds = Credentials(url=url, api_key=api_key)
                model = ModelInference(
                    model_id=attempt_model,
                    credentials=creds,
                    project_id=project_id,
                    params={
                        GP.MAX_NEW_TOKENS:     tokens,
                        GP.TEMPERATURE:        temperature,
                        GP.REPETITION_PENALTY: 1.15,
                        GP.TOP_P:              0.9,
                        GP.STOP_SEQUENCES:     ["<|user|>", "Human:", "User:"],
                    },
                )
                full_prompt = _build_prompt(attempt_model)
                response    = model.generate_text(prompt=full_prompt)
                if attempt_model != model_id:
                    logger.info(f"Used fallback model: {attempt_model}")
                text = response.strip()
                # Strip any repeated prompt echoing from base models
                if "### Response:" in text:
                    text = text.split("### Response:")[-1].strip()
                return text if text else self._smart_demo(prompt)
            except Exception as e:
                logger.warning(f"Model {attempt_model} failed: {e}")
                continue

        logger.error("All Granite model attempts failed — using smart demo.")
        return self._smart_demo(prompt)

    # ── Smart demo responses (input-aware, varied) ────────────────────────────

    def _smart_demo(self, prompt: str) -> str:
        """
        Generate varied, input-aware demo responses when the API is unavailable.
        Uses a stable hash of key terms so the same input always maps to the
        same template variant (deterministic), but different inputs produce
        different outputs.
        """
        p = prompt.lower()

        # Extract key signals from the prompt
        duration  = self._extract_duration(p)
        level     = self._extract_level(p)
        location  = self._extract_location(p)
        intensity = "high" if any(w in p for w in ["intense","advanced","hard","challenging"]) \
                    else "low" if any(w in p for w in ["easy","gentle","beginner","low","tired"]) \
                    else "medium"
        # Hash the prompt to pick a stable variant (0, 1, or 2)
        variant = int(hashlib.md5(prompt.encode()).hexdigest(), 16) % 3

        # ── Workout ──────────────────────────────────────────────────────────
        if any(w in p for w in ["workout", "exercise", "routine", "plan", "train"]):
            return self._workout_demo(duration, level, location, intensity, variant)

        # ── Meal / food ───────────────────────────────────────────────────────
        if any(w in p for w in ["meal", "food", "recipe", "eat", "cook", "diet",
                                  "breakfast", "lunch", "dinner", "snack"]):
            return self._meal_demo(p, variant)

        # ── Habit ─────────────────────────────────────────────────────────────
        if "habit" in p:
            return self._habit_demo(variant)

        # ── Motivation ────────────────────────────────────────────────────────
        if any(w in p for w in ["motivat", "inspire", "encourage", "push",
                                  "challeng", "keep going"]):
            return self._motivation_demo(variant)

        # ── Progress / summary ────────────────────────────────────────────────
        if any(w in p for w in ["progress", "summary", "achievement", "streak",
                                  "week", "trend"]):
            return self._progress_demo(p)

        # ── Generic ───────────────────────────────────────────────────────────
        return (
            "Welcome to Fitness Buddy! I'm here to help with:\n\n"
            "- Personalized workout plans for any time and energy level\n"
            "- Practical meal ideas using ingredients you already have\n"
            "- Progressive habit building (one step at a time)\n"
            "- Daily motivation matched to your coaching style\n"
            "- Progress tracking beyond the scale\n\n"
            "What would you like help with today?"
        )

    # ── Demo sub-generators ───────────────────────────────────────────────────

    def _extract_duration(self, p: str) -> int:
        for token in p.split():
            if token.isdigit():
                v = int(token)
                if 3 <= v <= 120:
                    return v
        if "5 min" in p:  return 5
        if "10 min" in p: return 10
        if "20 min" in p: return 20
        if "30 min" in p: return 30
        if "45 min" in p: return 45
        return 20  # default

    def _extract_level(self, p: str) -> str:
        if any(w in p for w in ["advanced", "expert", "athlete"]): return "advanced"
        if any(w in p for w in ["intermediate", "regular"]):        return "intermediate"
        return "beginner"

    def _extract_location(self, p: str) -> str:
        if "gym" in p:           return "gym"
        if "office" in p:        return "office"
        if "outdoor" in p:       return "outdoors"
        if "apartment" in p:     return "apartment"
        return "home"

    def _workout_demo(self, duration: int, level: str, location: str,
                      intensity: str, variant: int) -> str:
        warmup = min(3, duration // 6 + 1)
        cooldown = min(3, duration // 8 + 1)
        main = duration - warmup - cooldown

        level_map = {
            "beginner":     {"squat": "10", "push": "6",  "plank": "20s", "bridge": "10"},
            "intermediate": {"squat": "15", "push": "12", "plank": "30s", "bridge": "15"},
            "advanced":     {"squat": "20", "push": "20", "plank": "60s", "bridge": "20"},
        }
        reps = level_map.get(level, level_map["beginner"])

        # Three workout variants
        workouts = [
            # Variant 0 — Strength focus
            (
                f"**Strength-Focused Workout** ({duration} min | {level.title()} | {location.title()})\n\n"
                f"**Warm-Up ({warmup} min)**\n"
                "- Jumping jacks x 20\n- Arm circles x 15\n- Leg swings x 10 each\n\n"
                f"**Main Workout ({main} min)**\n"
                f"1. Bodyweight Squats - 3 x {reps['squat']} reps\n"
                f"2. Push-Ups - 3 x {reps['push']} reps\n"
                f"3. Glute Bridges - 3 x {reps['bridge']} reps\n"
                f"4. Plank Hold - 3 x {reps['plank']}\n"
                "5. Tricep Dips (chair) - 3 x 12 reps\n\n"
                f"**Cool Down ({cooldown} min)**\n"
                "- Quad stretch 30s each\n- Child's pose 30s\n- Shoulder stretch 20s each\n\n"
                f"**Note:** Rest 45s between sets. Adjust reps to match your energy today."
            ),
            # Variant 1 — Cardio focus
            (
                f"**Cardio + Core Workout** ({duration} min | {level.title()} | {location.title()})\n\n"
                f"**Warm-Up ({warmup} min)**\n"
                "- March in place 1 min\n- Hip circles x 10\n- Shoulder rolls x 10\n\n"
                f"**Main Workout ({main} min)**\n"
                f"1. High Knees - 3 x 30 seconds\n"
                f"2. Mountain Climbers - 3 x {reps['push']} reps\n"
                f"3. Plank to Downward Dog - 3 x 10 reps\n"
                f"4. Jump Squats (or squat pulses) - 3 x {reps['squat']} reps\n"
                "5. Bicycle Crunches - 3 x 15 reps each side\n\n"
                f"**Cool Down ({cooldown} min)**\n"
                "- Cat-cow stretch x 10\n- Seated forward fold 30s\n- Deep breathing 1 min\n\n"
                "**Note:** Keep heart rate moderate. Swap jumps for low-impact if needed."
            ),
            # Variant 2 — Mobility + strength
            (
                f"**Mobility + Functional Workout** ({duration} min | {level.title()} | {location.title()})\n\n"
                f"**Warm-Up ({warmup} min)**\n"
                "- Neck rolls x 8\n- World's greatest stretch x 5 each\n- Ankle circles x 10\n\n"
                f"**Main Workout ({main} min)**\n"
                f"1. Reverse Lunges - 3 x {reps['squat']} each leg\n"
                f"2. Push-Up to T-Rotation - 3 x {reps['push']} reps\n"
                f"3. Single-Leg Glute Bridge - 3 x {reps['bridge']} each\n"
                f"4. Dead Bug - 3 x 10 reps\n"
                "5. Side-Lying Hip Abductions - 3 x 15 each side\n\n"
                f"**Cool Down ({cooldown} min)**\n"
                "- Pigeon pose 45s each\n- Doorway chest stretch 30s\n- Child's pose 30s\n\n"
                "**Note:** Focus on form. Quality reps beat quantity every time."
            ),
        ]
        return workouts[variant]

    def _meal_demo(self, p: str, variant: int) -> str:
        # Detect ingredients mentioned in the prompt
        indian_ingredients = ["rice", "dal", "paneer", "roti", "poha", "chana",
                               "sprout", "curd", "egg", "potato", "onion", "tomato",
                               "vegetable", "lentil", "bread", "oat", "milk", "banana"]
        found = [i for i in indian_ingredients if i in p]
        base_note = f"Using: {', '.join(found[:4])}" if found else "Quick & nutritious options"

        meals = [
            # Variant 0 — Dal-based
            (
                f"**Meal Suggestions** ({base_note})\n\n"
                "**Option 1: Dal Tadka + Roti**\n"
                "- Cook yellow dal with turmeric, cumin, garlic tadka\n"
                "- Serve with 2 whole wheat rotis\n"
                "- Pair with sliced cucumber\n"
                "- Protein: ~18g | Time: 20 min | Budget: Low\n\n"
                "**Option 2: Egg Bhurji + Toast**\n"
                "- Scramble 2 eggs with onion, tomato, cumin, coriander\n"
                "- Serve on 2 slices whole grain bread\n"
                "- Side: glass of buttermilk\n"
                "- Protein: ~16g | Time: 10 min | Budget: Very low"
            ),
            # Variant 1 — Poha/chana based
            (
                f"**Meal Suggestions** ({base_note})\n\n"
                "**Option 1: Masala Poha**\n"
                "- Rinse poha, temper mustard seeds, curry leaves, green chilli\n"
                "- Add onion, peas, turmeric, lemon juice\n"
                "- Garnish with coriander and pomegranate seeds\n"
                "- Calories: ~250 | Time: 15 min | Budget: Low\n\n"
                "**Option 2: Chana Chaat**\n"
                "- Boiled chickpeas with diced onion, tomato, cucumber\n"
                "- Season: chaat masala, lemon, coriander, green chilli\n"
                "- Serve with mint chutney\n"
                "- Protein: ~14g | Time: 10 min (with canned chana)"
            ),
            # Variant 2 — Paneer/curd based
            (
                f"**Meal Suggestions** ({base_note})\n\n"
                "**Option 1: Paneer Bhurji + Rice**\n"
                "- Crumble paneer, saute with onion, tomato, capsicum, spices\n"
                "- Serve with 1 cup steamed rice\n"
                "- Side: raita (curd + cucumber + cumin)\n"
                "- Protein: ~22g | Time: 20 min | Budget: Medium\n\n"
                "**Option 2: Curd Rice**\n"
                "- Mix cooked rice with thick curd, salt, mustard seeds tadka\n"
                "- Add grated carrot and pomegranate for crunch\n"
                "- Great for digestion and a hot day\n"
                "- Calories: ~280 | Time: 5 min | Budget: Very low"
            ),
        ]
        return meals[variant]

    def _habit_demo(self, variant: int) -> str:
        habits = [
            (
                "**Today's Habit Coaching**\n\n"
                "Your focus: **Drink one extra glass of water** right after waking up.\n\n"
                "**Why this works:** Starting your day with hydration kickstarts metabolism, "
                "improves concentration, and sets a positive tone. It takes 5 seconds and "
                "costs nothing.\n\n"
                "**Your commitment:** Before opening your phone tomorrow morning, drink one "
                "full glass of water. That's it. One action, every morning.\n\n"
                "**Progress tracking:** Mark this done in the Habit Ladder after you complete it."
            ),
            (
                "**Today's Habit Coaching**\n\n"
                "Your focus: **5-minute walk after your next meal.**\n\n"
                "**Why this works:** Post-meal walks reduce blood sugar spikes by up to 12%, "
                "improve digestion, and create a consistent movement anchor tied to something "
                "you already do daily (eating).\n\n"
                "**Your commitment:** After lunch or dinner today — just 5 minutes outside "
                "or even around your home. No shoes required for indoors.\n\n"
                "**Make it stick:** Leave your shoes by the dining table as a visual cue."
            ),
            (
                "**Today's Habit Coaching**\n\n"
                "Your focus: **3-minute morning mobility** before you look at your phone.\n\n"
                "**Why this works:** Your body is stiff after 7-8 hours of sleep. Three minutes "
                "of gentle movement signals your nervous system that it's time to be alert and "
                "active — better than caffeine for waking up your body.\n\n"
                "**Your routine:**\n"
                "- Neck rolls x 5 each direction (30s)\n"
                "- Hip circles x 10 (30s)\n"
                "- Reach overhead + side bend x 5 each (1 min)\n"
                "- Ankle rolls x 10 each (30s)\n"
                "- Take 3 deep belly breaths (30s)\n\n"
                "**Do this tomorrow.** Just once. See how you feel."
            ),
        ]
        return habits[variant]

    def _motivation_demo(self, variant: int) -> str:
        messages = [
            (
                "You showed up. That already puts you ahead of the version of yourself "
                "who stayed on the couch.\n\n"
                "Here's the truth about fitness: it's not built in the moments of peak "
                "motivation. It's built in the ordinary moments when you do it anyway — "
                "tired, busy, stressed, unsure.\n\n"
                "**One action for today:** Do 10 squats right now. Not later. Now. "
                "That's it. Ten squats. You'll feel better immediately."
            ),
            (
                "Progress is not always visible. Some days you'll feel exactly the same "
                "as last week — but your cells adapted, your endurance grew, your habits "
                "deepened. The compound effect is invisible until it's undeniable.\n\n"
                "**Think about it:** If you improve just 1% every week, you're 52% better "
                "by the end of the year. That's not motivation math. That's biology.\n\n"
                "**Your challenge:** Do one thing for your health today that future-you will "
                "be grateful for. A walk, a glass of water, a stretch — pick one."
            ),
            (
                "The all-or-nothing mindset is the enemy of consistency. You don't have to "
                "do a perfect workout. You don't have to eat a perfect meal. You just have "
                "to do *something*.\n\n"
                "A 5-minute walk is better than no walk. A handful of fruit is better than "
                "skipping nutrition. Showing up imperfectly beats waiting for perfect.\n\n"
                "**Today's reframe:** Instead of 'I don't have time for a workout,' try "
                "'What's the smallest version of a workout I can do right now?' "
                "Even 3 minutes of movement rewires your brain to see yourself as someone "
                "who exercises."
            ),
        ]
        return messages[variant]

    def _progress_demo(self, p: str) -> str:
        return (
            "**Your Progress This Week**\n\n"
            "Progress in fitness is multi-dimensional. Here's what matters beyond the scale:\n\n"
            "**Consistency beats intensity:**\n"
            "Showing up 4 times at moderate effort outperforms 1 brutal session per week. "
            "Your goal: be active most days, not perfectly active some days.\n\n"
            "**What to track:**\n"
            "- Active days per week (target: 4-5)\n"
            "- Energy level trends (track in Check-In daily)\n"
            "- Habit streak (visible in Habit Ladder)\n"
            "- Total active minutes (compound over time)\n\n"
            "**Non-scale victories to celebrate:**\n"
            "- Climbing stairs without getting winded\n"
            "- Sleeping better\n"
            "- Feeling less stressed after a workout\n"
            "- Choosing a healthier meal more often\n\n"
            "Keep checking in daily — the data builds a picture over weeks, not days."
        )


def get_client() -> "GraniteClient":
    """Create a fresh GraniteClient (always reads latest .env)."""
    return GraniteClient()
