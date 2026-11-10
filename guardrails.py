"""
Guardrails Module — Fitness Buddy
Implements all 9 categories of guardrails for safe AI operation.
"""

import os
import re
import time
import json
import logging
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# 1. INPUT GUARDRAILS
# ─────────────────────────────────────────────────────────────

# Patterns that indicate prompt injection attempts
PROMPT_INJECTION_PATTERNS = [
    r"ignore (previous|above|all|your) (instructions?|prompts?|rules?)",
    r"forget (everything|all|your instructions)",
    r"you are now",
    r"new (persona|role|instructions?)",
    r"disregard (all|previous|your)",
    r"act as (if you are|a different|an unrestricted)",
    r"jailbreak",
    r"do anything now",
    r"dan mode",
    r"developer mode",
    r"bypass (filter|restriction|guardrail)",
    r"pretend (you have no|there are no) (restrictions?|rules?|filters?)",
    r"reveal (your|the) (system prompt|instructions|api key|secret)",
    r"print (your|the) (system prompt|instructions)",
    r"what (are|is) your (instructions?|system prompt|rules?)",
    r"ignore all (previous|above|your)",
    r"ignore (and|my|your|these) instructions",
    r"override (your|the|all) (instructions?|settings?|rules?)",
]

# SQL injection patterns — require unambiguous SQL syntax context.
# Only match multi-word SQL keywords (e.g. "DROP TABLE", "SELECT ... FROM")
# or chained statements after semicolons. Never match single English words
# like SELECT, CREATE, DROP, INSERT, DELETE on their own.
SQL_INJECTION_PATTERNS = [
    # Multi-word SQL DML/DDL that cannot appear in normal fitness prose
    r"\bINSERT\s+INTO\b",
    r"\bUPDATE\s+\w+\s+SET\b",
    r"\bDELETE\s+FROM\b",
    r"\bDROP\s+(TABLE|DATABASE|INDEX|VIEW)\b",
    r"\bTRUNCATE\s+TABLE\b",
    r"\bALTER\s+TABLE\b",
    r"\bCREATE\s+(TABLE|DATABASE|INDEX|VIEW|PROCEDURE)\b",
    r"\bSELECT\b.{0,80}\bFROM\b",          # SELECT ... FROM (SQL query shape)
    # Boolean-based injection probes
    r"OR\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?",   # OR '1'='1'  OR 1=1
    r"AND\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?",  # AND 1=1
    r"UNION\s+(ALL\s+)?SELECT\b",
    # Block comments (never valid in plain text)
    r"/\*[\s\S]*?\*/",
    # Stored-procedure execution
    r"\bxp_cmdshell\b",
    r"\bexec\s*\(\s*['\"]",
    # Chained destructive statement after semicolon
    r";\s*(DROP|DELETE\s+FROM|INSERT\s+INTO|UPDATE\s+\w+\s+SET|TRUNCATE)\b",
]

# Malicious / harmful content patterns
HARMFUL_CONTENT_PATTERNS = [
    r"\b(harm|kill|murder|suicide|self.harm|overdose)\b",
    r"\b(bomb|explosive|weapon|poison|drug trafficking)\b",
    r"\b(hack|exploit|malware|ransomware|phishing)\b",
]

# PII patterns
PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(\+?1?\s?)?(\(?\d{3}\)?[\s.-]?)(\d{3}[\s.-]?)(\d{4})\b",
    "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "aadhaar": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "pan_card": r"\b[A-Z]{5}\d{4}[A-Z]\b",
    "passport": r"\b[A-Z]\d{7}\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
}

# Inappropriate fitness-unrelated topics
OFF_TOPIC_PATTERNS = [
    r"\b(political|religion|vote|election|gambling|stock market|cryptocurrency)\b",
    r"\b(sex|porn|adult content|nude|naked)\b",
]

# Medical / clinical claims that should be blocked
MEDICAL_CLAIM_PATTERNS = [
    r"\b(diagnose|diagnosis|cure|treat|prescription|medication|medical advice)\b",
    r"\b(guaranteed weight loss|clinically proven|medically approved)\b",
]


class InputGuardrails:
    """Validates and sanitizes user inputs before AI processing."""

    def __init__(self):
        self.max_length = int(os.getenv("MAX_INPUT_LENGTH", "2000"))
        self.enable_pii = os.getenv("ENABLE_PII_DETECTION", "True").lower() == "true"

    def validate(self, user_input: str) -> Tuple[bool, str, str]:
        """
        Validate user input.
        Returns: (is_valid, sanitized_input, rejection_reason)
        """
        if not user_input or not user_input.strip():
            return False, "", "Input cannot be empty."

        # Length check
        if len(user_input) > self.max_length:
            return False, "", f"Input too long. Maximum {self.max_length} characters allowed."

        # Sanitize HTML/script tags
        sanitized = self._sanitize_html(user_input)

        # Prompt injection detection
        injection_found, injection_detail = self._detect_prompt_injection(sanitized)
        if injection_found:
            logger.warning(f"Prompt injection detected: {injection_detail}")
            return False, "", "Your message contains content that cannot be processed. Please rephrase."

        # SQL injection detection
        sql_found = self._detect_sql_injection(sanitized)
        if sql_found:
            logger.warning("SQL injection attempt detected.")
            return False, "", "Your message contains invalid characters or patterns."

        # Harmful content detection
        harmful_found, harmful_detail = self._detect_harmful_content(sanitized)
        if harmful_found:
            logger.warning(f"Harmful content detected: {harmful_detail}")
            return False, "", (
                "I'm a fitness assistant and can't respond to that topic. "
                "If you're in distress, please contact a helpline: iCall 9152987821."
            )

        # PII detection
        if self.enable_pii:
            pii_found, pii_types = self._detect_pii(sanitized)
            if pii_found:
                sanitized = self._redact_pii(sanitized)
                logger.info(f"PII detected and redacted: {pii_types}")

        # Off-topic filtering
        off_topic, off_detail = self._detect_off_topic(sanitized)
        if off_topic:
            return False, "", (
                "I'm focused on fitness, nutrition, and healthy habits. "
                "Please ask me something related to your wellness journey!"
            )

        return True, sanitized.strip(), ""

    def _sanitize_html(self, text: str) -> str:
        """Remove HTML/script injection attempts."""
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"&[a-z]+;", " ", text)
        return text

    def _detect_prompt_injection(self, text: str) -> Tuple[bool, str]:
        text_lower = text.lower()
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, pattern
        return False, ""

    def _detect_sql_injection(self, text: str) -> bool:
        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _detect_harmful_content(self, text: str) -> Tuple[bool, str]:
        text_lower = text.lower()
        for pattern in HARMFUL_CONTENT_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, pattern
        return False, ""

    def _detect_pii(self, text: str) -> Tuple[bool, List[str]]:
        found_types = []
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, text):
                found_types.append(pii_type)
        return len(found_types) > 0, found_types

    def _redact_pii(self, text: str) -> str:
        for pii_type, pattern in PII_PATTERNS.items():
            label = f"[{pii_type.upper()}_REDACTED]"
            text = re.sub(pattern, label, text)
        return text

    def _detect_off_topic(self, text: str) -> Tuple[bool, str]:
        text_lower = text.lower()
        for pattern in OFF_TOPIC_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, pattern
        return False, ""


# ─────────────────────────────────────────────────────────────
# 2. OUTPUT GUARDRAILS
# ─────────────────────────────────────────────────────────────

TOXIC_OUTPUT_PATTERNS = [
    r"\b(idiot|stupid|loser|fat|ugly|worthless|pathetic)\b",
    r"\b(kill yourself|you should die|hate you)\b",
]

# Only match when an actual secret VALUE is adjacent (e.g. "api_key=abc123"),
# never the plain English word "credentials" in an instruction sentence.
SENSITIVE_OUTPUT_PATTERNS = [
    r"(?:api[_\s]?key|secret[_\s]?key|password)\s*[=:]\s*\S+",   # key=value pairs
    r"Bearer\s+[a-zA-Z0-9._\-]{20,}",                             # real Bearer tokens
    r"sk-[a-zA-Z0-9]{20,}",                                       # OpenAI-style keys
    r"eyJ[a-zA-Z0-9_\-]{30,}",                                    # raw JWT tokens
]

HALLUCINATION_INDICATORS = [
    r"\b(as of \d{4}|according to my training|I cannot verify|I am not sure|I don't know)\b",
    r"\b(may not be accurate|consult a (doctor|physician|dietitian|nutritionist))\b",
]

REQUIRED_DISCLAIMER_TOPICS = [
    "weight loss", "diet plan", "medical", "injury", "pain", "disease",
    "diabetes", "hypertension", "pregnancy", "cancer",
]


class OutputGuardrails:
    """Validates AI-generated responses before showing them to users."""

    def __init__(self):
        self.enable_toxicity = os.getenv("ENABLE_TOXICITY_FILTER", "True").lower() == "true"
        self.enable_hallucination = os.getenv("ENABLE_HALLUCINATION_CHECK", "True").lower() == "true"

    def validate(self, response: str, original_prompt: str = "") -> Tuple[bool, str, List[str]]:
        """
        Validate AI response.
        Returns: (is_valid, cleaned_response, warnings)
        """
        warnings = []

        if not response or len(response.strip()) < 10:
            return False, "I wasn't able to generate a response. Please try again.", warnings

        cleaned = response

        # Toxicity filtering
        if self.enable_toxicity:
            cleaned, toxic_removed = self._filter_toxicity(cleaned)
            if toxic_removed:
                warnings.append("Some inappropriate language was removed from the response.")

        # Sensitive information filtering
        cleaned, sensitive_removed = self._filter_sensitive_info(cleaned)
        if sensitive_removed:
            warnings.append("Sensitive information was filtered from the response.")
            logger.warning("Sensitive info found in AI output — filtered.")

        # Medical claim detection → append disclaimer
        needs_disclaimer, disclaimer_topic = self._needs_medical_disclaimer(cleaned)
        if needs_disclaimer:
            cleaned = self._append_disclaimer(cleaned, disclaimer_topic)

        # Hallucination indicator tagging
        if self.enable_hallucination:
            hallucination_risk = self._check_hallucination_risk(cleaned)
            if hallucination_risk:
                warnings.append("Note: Some information may require verification with a professional.")

        # Validate response is fitness-relevant
        if not self._is_fitness_relevant(cleaned, original_prompt):
            warnings.append("Response may be off-topic. Returning safe fallback.")
            return False, self._safe_fallback(), warnings

        # Format validation — ensure response is readable text
        cleaned = self._validate_format(cleaned)

        return True, cleaned, warnings

    def _filter_toxicity(self, text: str) -> Tuple[str, bool]:
        removed = False
        for pattern in TOXIC_OUTPUT_PATTERNS:
            new_text = re.sub(pattern, "[removed]", text, flags=re.IGNORECASE)
            if new_text != text:
                removed = True
                text = new_text
        return text, removed

    def _filter_sensitive_info(self, text: str) -> Tuple[str, bool]:
        removed = False
        for pattern in SENSITIVE_OUTPUT_PATTERNS:
            new_text = re.sub(pattern, "[FILTERED]", text, flags=re.IGNORECASE)
            if new_text != text:
                removed = True
                text = new_text
        return text, removed

    def _needs_medical_disclaimer(self, text: str) -> Tuple[bool, str]:
        text_lower = text.lower()
        for topic in REQUIRED_DISCLAIMER_TOPICS:
            if topic in text_lower:
                return True, topic
        return False, ""

    def _append_disclaimer(self, text: str, topic: str) -> str:
        disclaimer = (
            "\n\n---\n"
            "⚠️ **Disclaimer:** This information is for general wellness purposes only and "
            "does not constitute medical advice. Please consult a qualified healthcare "
            "professional before making significant changes to your diet, exercise routine, "
            "or if you have any medical conditions."
        )
        if disclaimer.strip() not in text:
            text += disclaimer
        return text

    def _check_hallucination_risk(self, text: str) -> bool:
        for pattern in HALLUCINATION_INDICATORS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _is_fitness_relevant(self, text: str, prompt: str) -> bool:
        """
        Return True if the response (or the originating prompt) contains
        any fitness-related content. We check the prompt first — if the
        user asked a fitness question the response is presumed relevant
        even if the model answered in a way that doesn't surface keywords.
        This prevents valid AI responses from being incorrectly replaced
        with the generic fallback.
        """
        fitness_keywords = [
            "workout", "exercise", "fitness", "health", "nutrition", "meal", "food",
            "habit", "routine", "stretch", "yoga", "run", "walk", "squat", "push",
            "plan", "goal", "energy", "sleep", "water", "protein", "cardio",
            "strength", "flexibility", "balance", "rest", "recovery", "motivation",
            "breathing", "mindfulness", "calorie", "vegetable", "fruit", "dal",
            "roti", "paneer", "step", "minute", "set", "rep", "beginner", "advanced",
            "intermediate", "warm", "cool", "equipment", "check", "progress", "habit",
            "coach", "guide", "welcome", "today", "level", "time", "duration",
        ]
        combined = (text + " " + prompt).lower()
        # If the prompt is fitness-related, accept the response unconditionally.
        # This stops the guardrail from swallowing valid model output.
        if any(kw in prompt.lower() for kw in fitness_keywords):
            return True
        return any(kw in combined for kw in fitness_keywords)

    def _validate_format(self, text: str) -> str:
        # Ensure no raw JSON leaks
        if text.strip().startswith("{") and text.strip().endswith("}"):
            try:
                data = json.loads(text)
                return json.dumps(data, indent=2)
            except Exception:
                pass
        return text

    def _safe_fallback(self) -> str:
        return (
            "I'm your Fitness Buddy! I can help you with:\n"
            "- 🏋️ Personalized workout plans\n"
            "- 🥗 Meal and nutrition suggestions\n"
            "- 💧 Habit building tips\n"
            "- 💪 Daily motivation\n\n"
            "What would you like help with today?"
        )


# ─────────────────────────────────────────────────────────────
# 3. TOOL EXECUTION GUARDRAILS
# ─────────────────────────────────────────────────────────────

ALLOWED_TOOLS = {
    "generate_workout": ["generate"],
    "generate_meal": ["generate"],
    "generate_habit": ["generate"],
    "generate_motivation": ["generate"],
    "calculate_score": ["compute"],
    "track_progress": ["read", "write"],
}


class ToolGuardrails:
    """Controls how AI agents interact with tools and APIs."""

    def __init__(self):
        self._tool_call_counts: Dict[str, int] = defaultdict(int)
        self._tool_call_window_start = time.time()
        self.rate_limit = int(os.getenv("RATE_LIMIT_CALLS", "10"))
        self.rate_period = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

    def authorize_tool(self, tool_name: str, action: str, user_role: str = "user") -> Tuple[bool, str]:
        """Check if a tool action is permitted for the given role."""
        if tool_name not in ALLOWED_TOOLS:
            return False, f"Tool '{tool_name}' is not registered."
        allowed_actions = ALLOWED_TOOLS[tool_name]
        if action not in allowed_actions:
            return False, f"Action '{action}' is not permitted for tool '{tool_name}'."
        # Rate limiting per tool
        if not self._check_rate_limit(tool_name):
            return False, "Rate limit exceeded. Please wait a moment before trying again."
        return True, "Authorized"

    def validate_function_call(self, function_name: str, params: Dict) -> Tuple[bool, str]:
        """Validate function call parameters before execution."""
        # Prevent dangerous parameter values
        for key, value in params.items():
            if isinstance(value, str):
                if re.search(r"(rm -rf|del /|format c:|os\.system|subprocess)", value, re.IGNORECASE):
                    return False, f"Dangerous parameter value detected in '{key}'."
                if len(value) > 5000:
                    return False, f"Parameter '{key}' exceeds maximum allowed length."
        return True, "Valid"

    def _check_rate_limit(self, tool_name: str) -> bool:
        now = time.time()
        if now - self._tool_call_window_start > self.rate_period:
            self._tool_call_counts.clear()
            self._tool_call_window_start = now
        self._tool_call_counts[tool_name] += 1
        return self._tool_call_counts[tool_name] <= self.rate_limit


# ─────────────────────────────────────────────────────────────
# 4. DATA GUARDRAILS
# ─────────────────────────────────────────────────────────────

SENSITIVE_FIELDS = {"weight", "age", "medical_conditions", "medications", "health_data"}

ROLE_ACCESS = {
    "user": {"read": {"profile", "progress", "workouts", "meals", "habits"}, "write": {"progress", "habits"}},
    "coach": {"read": {"profile", "progress", "workouts", "meals", "habits"}, "write": {"workouts", "meals"}},
    "admin": {"read": {"*"}, "write": {"*"}},
}


class DataGuardrails:
    """Protects data accessed and processed by the agent."""

    def check_access(self, role: str, resource: str, action: str) -> Tuple[bool, str]:
        """Role-based data access control."""
        role_perms = ROLE_ACCESS.get(role, {})
        allowed = role_perms.get(action, set())
        if "*" in allowed or resource in allowed:
            return True, "Access granted"
        return False, f"Role '{role}' does not have {action} access to '{resource}'."

    def anonymize(self, data: Dict) -> Dict:
        """Anonymize sensitive fields before logging or storing."""
        anonymized = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_FIELDS:
                if isinstance(value, str):
                    anonymized[key] = hashlib.sha256(value.encode()).hexdigest()[:8] + "***"
                else:
                    anonymized[key] = "***"
            else:
                anonymized[key] = value
        return anonymized

    def mask_pii_in_logs(self, log_entry: str) -> str:
        """Mask PII before writing to logs."""
        for pii_type, pattern in PII_PATTERNS.items():
            log_entry = re.sub(pattern, f"[{pii_type.upper()}]", log_entry)
        return log_entry

    def validate_db_query(self, query: str) -> Tuple[bool, str]:
        """Prevent unauthorized or dangerous DB queries."""
        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "Potentially dangerous query pattern detected."
        dangerous_ops = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE"]
        for op in dangerous_ops:
            if op in query.upper():
                return False, f"Operation '{op}' is not allowed."
        return True, "Query validated"


# ─────────────────────────────────────────────────────────────
# 5. SECURITY GUARDRAILS
# ─────────────────────────────────────────────────────────────

JAILBREAK_PATTERNS = [
    r"(grand)?mother(\s+told|\s+used to|\s+always said)",  # grandma jailbreak
    r"story|roleplay|fiction|hypothetically|let's pretend|imagine you",
    r"as a (fictional|virtual|unlimited|unrestricted) ai",
    r"(evil|dark|shadow|uncensored|unfiltered) (mode|version|ai|model)",
    r"token\s+limit\s+removal",
]


class SecurityGuardrails:
    """Protects against security threats."""

    def __init__(self):
        self._failed_attempts: Dict[str, List[float]] = defaultdict(list)

    def detect_jailbreak(self, text: str) -> Tuple[bool, str]:
        text_lower = text.lower()
        for pattern in JAILBREAK_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, f"Jailbreak pattern detected: {pattern}"
        return False, ""

    def validate_credentials(self, api_key: str) -> Tuple[bool, str]:
        """Validate API key format before use."""
        if not api_key:
            return False, "API key is missing."
        if len(api_key) < 20:
            return False, "API key appears to be malformed."
        # Prevent accidental exposure
        if api_key.lower() in ["your_ibm_api_key_here", "test", "demo", "fake"]:
            return False, "Placeholder API key detected. Please configure a real key."
        return True, "Valid"

    def record_failed_attempt(self, session_id: str):
        """Track failed security attempts per session."""
        now = time.time()
        self._failed_attempts[session_id] = [
            t for t in self._failed_attempts[session_id] if now - t < 300
        ]
        self._failed_attempts[session_id].append(now)

    def is_blocked(self, session_id: str, max_attempts: int = 5) -> bool:
        """Block session after too many failed attempts."""
        return len(self._failed_attempts.get(session_id, [])) >= max_attempts


# ─────────────────────────────────────────────────────────────
# 6. OPERATIONAL GUARDRAILS
# ─────────────────────────────────────────────────────────────

class OperationalGuardrails:
    """Controls agent execution and resource consumption."""

    def __init__(self):
        self.max_exec_time = int(os.getenv("MAX_EXECUTION_TIME_SECONDS", "30"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.max_iterations = 5
        self._api_calls_today: Dict[str, int] = defaultdict(int)
        self._api_call_date: str = datetime.now().strftime("%Y-%m-%d")

    def execution_timeout(self, func):
        """Decorator to enforce execution time limits."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            import threading
            result = [None]
            error = [None]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    error[0] = e

            thread = threading.Thread(target=target)
            thread.start()
            thread.join(timeout=self.max_exec_time)

            if thread.is_alive():
                logger.error("Execution timeout exceeded.")
                return "Request timed out. Please try a simpler query."

            if error[0]:
                raise error[0]
            return result[0]
        return wrapper

    def track_api_call(self, service: str, estimated_cost: float = 0.0) -> Tuple[bool, str]:
        """Track API usage and enforce daily limits."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._api_call_date:
            self._api_calls_today.clear()
            self._api_call_date = today

        daily_limit = 500  # Conservative limit for IBM Lite tier
        self._api_calls_today[service] += 1
        count = self._api_calls_today[service]

        if count > daily_limit:
            return False, f"Daily API limit ({daily_limit}) reached for {service}."
        if count > daily_limit * 0.8:
            logger.warning(f"API usage at {count}/{daily_limit} for {service} today.")
        return True, f"API call {count}/{daily_limit}"

    def retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                wait_time = 2 ** attempt
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
        raise last_error


# ─────────────────────────────────────────────────────────────
# 7. HUMAN-IN-THE-LOOP GUARDRAILS
# ─────────────────────────────────────────────────────────────

CRITICAL_ACTIONS = {
    "delete_all_progress": "This will permanently delete all your fitness progress data.",
    "share_health_data": "This will share your health data with external services.",
    "reset_habits": "This will reset your entire habit tracking history.",
    "export_data": "This will export all your personal fitness data.",
}


class HumanInLoopGuardrails:
    """Ensures human approval for critical decisions."""

    def requires_approval(self, action: str) -> Tuple[bool, str]:
        """Check if an action requires human confirmation."""
        if action in CRITICAL_ACTIONS:
            return True, CRITICAL_ACTIONS[action]
        return False, ""

    def escalation_needed(self, response: str) -> Tuple[bool, str]:
        """
        Detect if response content warrants escalation to a human expert.
        E.g., medical symptoms mentioned.
        """
        escalation_triggers = [
            r"\b(chest pain|shortness of breath|dizziness|fainting|severe pain)\b",
            r"\b(heart attack|stroke|emergency|call 911|ambulance)\b",
            r"\b(eating disorder|anorexia|bulimia|binge eating)\b",
            r"\b(suicidal|self-harm|cutting|overdose)\b",
        ]
        for pattern in escalation_triggers:
            if re.search(pattern, response, re.IGNORECASE):
                return True, (
                    "⚠️ **Important:** The content you've described may require professional attention. "
                    "Please consult a qualified healthcare professional or call emergency services if needed.\n"
                    "**Mental health support (India):** iCall — 9152987821\n"
                    "**Emergency:** 112"
                )
        return False, ""


# ─────────────────────────────────────────────────────────────
# 8. MULTI-AGENT GUARDRAILS
# ─────────────────────────────────────────────────────────────

AGENT_ROLES = {
    "workout_agent": ["generate_workout", "modify_workout"],
    "nutrition_agent": ["generate_meal", "suggest_recipe"],
    "habit_agent": ["create_habit", "track_habit"],
    "motivation_agent": ["generate_motivation", "send_reminder"],
    "progress_agent": ["read_progress", "write_progress", "calculate_score"],
}


class MultiAgentGuardrails:
    """Ensures safe coordination between multiple specialized agents."""

    def __init__(self):
        self._agent_iterations: Dict[str, int] = defaultdict(int)
        self.max_iterations = int(os.getenv("MAX_AGENT_ITERATIONS", "5"))

    def authorize_agent_action(self, agent_id: str, action: str) -> Tuple[bool, str]:
        """Agent-level access control."""
        allowed = AGENT_ROLES.get(agent_id, [])
        if action not in allowed:
            return False, f"Agent '{agent_id}' is not authorized for action '{action}'."
        return True, "Authorized"

    def validate_agent_output(self, agent_id: str, output: Any) -> Tuple[bool, str]:
        """Validate output before passing between agents."""
        if output is None:
            return False, f"Agent '{agent_id}' returned null output."
        if isinstance(output, str) and len(output) > 10000:
            return False, "Agent output exceeds maximum allowed size."
        return True, "Valid"

    def check_iteration_limit(self, task_id: str) -> Tuple[bool, str]:
        """Prevent infinite agent loops."""
        self._agent_iterations[task_id] += 1
        count = self._agent_iterations[task_id]
        if count > self.max_iterations:
            return False, f"Maximum iterations ({self.max_iterations}) reached for task '{task_id}'."
        return True, f"Iteration {count}/{self.max_iterations}"

    def verify_cross_agent_message(self, sender: str, receiver: str, message: Dict) -> Tuple[bool, str]:
        """Validate messages passed between agents."""
        if sender not in AGENT_ROLES:
            return False, f"Unknown sender agent: '{sender}'."
        if receiver not in AGENT_ROLES:
            return False, f"Unknown receiver agent: '{receiver}'."
        if not isinstance(message, dict):
            return False, "Inter-agent message must be a dictionary."
        required_keys = {"task_id", "payload"}
        if not required_keys.issubset(message.keys()):
            return False, f"Message missing required keys: {required_keys - message.keys()}"
        return True, "Valid"


# ─────────────────────────────────────────────────────────────
# 9. ETHICAL & COMPLIANCE GUARDRAILS
# ─────────────────────────────────────────────────────────────

class EthicalGuardrails:
    """Ensures responsible and compliant AI behaviour."""

    def __init__(self):
        self._audit_log: List[Dict] = []

    def detect_bias(self, response: str) -> Tuple[bool, str]:
        """Detect potentially biased language in AI responses."""
        bias_patterns = [
            r"\b(women (can't|cannot|shouldn't|don't)|men are (better|stronger|superior))\b",
            r"\b(old people (can't|cannot|shouldn't)|young people (always|never))\b",
            r"\b(fat (people|persons)|skinny (people|persons))\b",
            r"\b(overweight (people|persons) (are|should|must))\b",
        ]
        for pattern in bias_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return True, f"Potential bias detected: {pattern}"
        return False, ""

    def validate_fairness(self, response: str, user_profile: Dict) -> str:
        """Ensure response is appropriate regardless of user demographics."""
        # Ensure inclusive language
        response = re.sub(
            r"\b(he|she) should\b",
            "you should",
            response,
            flags=re.IGNORECASE,
        )
        return response

    def explain_recommendation(self, recommendation: str, reasoning: str) -> str:
        """Add explainability to AI recommendations."""
        return f"{recommendation}\n\n*Why this recommendation: {reasoning}*"

    def check_regulatory_compliance(self, response: str) -> Tuple[bool, List[str]]:
        """
        Check for content that might violate regulations.
        Flags medical claims, guaranteed results, etc.
        """
        violations = []
        regulated_patterns = [
            (r"\b(guaranteed|proven|clinically proven)\b", "Unsubstantiated health claim"),
            (r"\b(cure|treat|diagnose|prescribe)\b", "Medical claim without disclaimer"),
            (r"\b(lose \d+ kg in \d+ (day|week)s?)\b", "Unrealistic weight loss claim"),
            (r"\b(FDA approved|FSSAI certified)\b", "Regulatory approval claim"),
        ]
        for pattern, violation_type in regulated_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(violation_type)
        return len(violations) == 0, violations

    def log_audit_trail(self, user_id: str, action: str, input_hash: str, output_hash: str):
        """Create immutable audit trail entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "guardrails_applied": [
                "input_validation", "pii_detection", "toxicity_filter",
                "output_validation", "compliance_check",
            ],
        }
        self._audit_log.append(entry)
        logger.info(f"Audit: {entry}")
        return entry

    def get_audit_log(self) -> List[Dict]:
        return self._audit_log.copy()


# ─────────────────────────────────────────────────────────────
# UNIFIED GUARDRAIL PIPELINE
# ─────────────────────────────────────────────────────────────

class GuardrailPipeline:
    """
    Unified guardrail pipeline that chains all guardrail checks
    for a complete request/response lifecycle.
    """

    def __init__(self):
        self.input_guardrails = InputGuardrails()
        self.output_guardrails = OutputGuardrails()
        self.tool_guardrails = ToolGuardrails()
        self.data_guardrails = DataGuardrails()
        self.security_guardrails = SecurityGuardrails()
        self.operational_guardrails = OperationalGuardrails()
        self.human_loop_guardrails = HumanInLoopGuardrails()
        self.multi_agent_guardrails = MultiAgentGuardrails()
        self.ethical_guardrails = EthicalGuardrails()

    def process_input(self, user_input: str, session_id: str = "default") -> Tuple[bool, str, str]:
        """
        Full input processing pipeline.
        Returns: (is_valid, sanitized_input, error_message)
        """
        # Security: jailbreak check
        jailbreak, jb_detail = self.security_guardrails.detect_jailbreak(user_input)
        if jailbreak:
            self.security_guardrails.record_failed_attempt(session_id)
            logger.warning(f"Jailbreak attempt from session {session_id}: {jb_detail}")
            return False, "", "I'm here to help with fitness and wellness only. Let's keep things positive!"

        # Security: check if session is blocked
        if self.security_guardrails.is_blocked(session_id):
            return False, "", "Too many invalid requests. Please start a new session."

        # Input validation
        valid, sanitized, error = self.input_guardrails.validate(user_input)
        if not valid:
            self.security_guardrails.record_failed_attempt(session_id)
            return False, "", error

        return True, sanitized, ""

    def process_output(self, response: str, original_prompt: str = "", user_profile: Dict = None) -> Tuple[str, List[str]]:
        """
        Full output processing pipeline.
        Returns: (final_response, warnings)
        """
        all_warnings = []

        # Output validation
        valid, cleaned, warnings = self.output_guardrails.validate(response, original_prompt)
        all_warnings.extend(warnings)
        if not valid:
            return cleaned, all_warnings  # cleaned is the safe fallback

        # Bias detection
        biased, bias_detail = self.ethical_guardrails.detect_bias(cleaned)
        if biased:
            logger.warning(f"Bias detected in output: {bias_detail}")
            all_warnings.append("Response was adjusted for inclusive language.")

        # Fairness validation
        if user_profile:
            cleaned = self.ethical_guardrails.validate_fairness(cleaned, user_profile)

        # Compliance check
        compliant, violations = self.ethical_guardrails.check_regulatory_compliance(cleaned)
        if not compliant:
            all_warnings.extend([f"Compliance note: {v}" for v in violations])
            cleaned = self.output_guardrails._append_disclaimer(cleaned, "compliance")

        # Human escalation check
        escalate, escalation_msg = self.human_loop_guardrails.escalation_needed(cleaned)
        if escalate:
            cleaned = escalation_msg + "\n\n" + cleaned

        # Audit trail
        input_hash = hashlib.sha256(original_prompt.encode()).hexdigest()[:16]
        output_hash = hashlib.sha256(cleaned.encode()).hexdigest()[:16]
        self.ethical_guardrails.log_audit_trail("session", "generate_response", input_hash, output_hash)

        return cleaned, all_warnings


# Singleton pipeline
_pipeline: Optional[GuardrailPipeline] = None


def get_pipeline() -> GuardrailPipeline:
    """Get or create the global guardrail pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = GuardrailPipeline()
    return _pipeline
