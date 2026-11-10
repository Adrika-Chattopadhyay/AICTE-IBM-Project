"""
Render the Fitness Buddy Architecture Blueprint as a high-quality PNG
using Pillow. No external C dependencies required.
"""
from PIL import Image, ImageDraw, ImageFont
import os, sys

W, H = 2100, 1290   # 1.5x scale for high-DPI
SCALE = 1.5

# ── colour palette ──────────────────────────────────────────────
BG          = "#f0f4f8"
NAVY        = "#0f2137"
BLUE        = "#1d4ed8"
BLUE2       = "#2563eb"
BLUE_LIGHT  = "#dbeafe"
BLUE_MID    = "#93c5fd"
TEAL        = "#0f766e"
TEAL_LIGHT  = "#ccfbf1"
TEAL_MID    = "#2dd4bf"
PURPLE      = "#7c3aed"
PURPLE_L    = "#f3e8ff"
PURPLE_M    = "#c084fc"
AMBER       = "#b45309"
AMBER_L     = "#fef3c7"
AMBER_M     = "#f59e0b"
RED         = "#dc2626"
RED_L       = "#fee2e2"
RED_M       = "#fca5a5"
SLATE       = "#374151"
SLATE_L     = "#f1f5f9"
SLATE_M     = "#94a3b8"
WHITE       = "#ffffff"
DARK        = "#111827"
MID         = "#6b7280"
LIGHT       = "#9ca3af"
BORD_BLUE   = "#3b82f6"
BORD_TEAL   = "#14b8a6"
INDIGO_L    = "#eff6ff"

def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def s(v): return int(v * SCALE)  # scale helper

def load_font(size):
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except Exception:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

def load_font_regular(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()

def rounded_rect(draw, x1, y1, x2, y2, radius, fill, outline=None, width=2):
    r = max(radius, 1)
    fill_rgb   = hex2rgb(fill)
    outline_rgb = hex2rgb(outline) if outline else None
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill_rgb,
                            outline=outline_rgb, width=width)

def text_centered(draw, text, cx, cy, font, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw//2, cy - th//2), text, font=font, fill=hex2rgb(color))

def text_left(draw, text, x, y, font, color):
    draw.text((x, y), text, font=font, fill=hex2rgb(color))

# ════════════════════════════════════════════════════════════════
img  = Image.new("RGB", (W, H), hex2rgb(BG))
draw = ImageDraw.Draw(img)

# fonts
F_TITLE   = load_font(28)
F_HEAD    = load_font(20)
F_SUBHEAD = load_font(16)
F_BODY    = load_font_regular(14)
F_SMALL   = load_font_regular(12)
F_TINY    = load_font_regular(11)
F_BADGE   = load_font(10)

# ── Title bar ────────────────────────────────────────────────────
draw.rectangle([0, 0, W, s(56)], fill=hex2rgb(NAVY))
text_centered(draw, "FITNESS BUDDY — ARCHITECTURE BLUEPRINT", W//2, s(22), F_TITLE, WHITE)
text_centered(draw, "IBM GRANITE · WATSONX.AI · STREAMLIT · 9-LAYER GUARDRAILS", W//2, s(45), F_SMALL, BLUE_MID)

# ── Row 1 — User Interface (y 72..184) ──────────────────────────
R1Y1, R1Y2 = s(72), s(184)
rounded_rect(draw, s(36), R1Y1, W - s(12), R1Y2, s(8), BLUE_LIGHT, BLUE_MID, 2)

# Streamlit App box
rounded_rect(draw, s(56), s(84), s(218), s(172), s(8), BLUE, NAVY, 2)
text_centered(draw, "Streamlit App", s(137), s(104), F_HEAD, WHITE)
text_centered(draw, "8 Pages · Wide Layout", s(137), s(124), F_SMALL, "#bfdbfe")
text_centered(draw, "app.py  |  Responsive CSS", s(137), s(142), F_TINY, BLUE_MID)
text_centered(draw, "per-render env reload", s(137), s(158), F_TINY, BLUE_MID)

pages = [
    ("Daily\nCheck-In", "Feature A+G", s(244)),
    ("Workout\nPlanner", "Feature B+C", s(348)),
    ("Meal\nBuilder", "Feature D", s(452)),
    ("Habit\nLadder", "Feature E", s(556)),
    ("Progress\nTracker", "Feature H", s(660)),
    ("AI Chat", "Granite Chat", s(764)),
    ("Home\nDashboard", "Feature A,F", s(868)),
    ("Guardrails\nPanel", "9 Layers", s(972)),
]
for label, sub, cx in pages:
    rounded_rect(draw, cx - s(44), s(84), cx + s(44), s(126), s(6), BLUE2, BORD_BLUE, 1)
    lines = label.split("\n")
    if len(lines) == 2:
        text_centered(draw, lines[0], cx, s(97), F_SMALL, WHITE)
        text_centered(draw, lines[1], cx, s(112), F_SMALL, WHITE)
    else:
        text_centered(draw, lines[0], cx, s(104), F_SMALL, WHITE)
    rounded_rect(draw, cx - s(44), s(132), cx + s(44), s(170), s(5), INDIGO_L, BLUE_MID, 1)
    text_centered(draw, sub, cx, s(154), F_TINY, BLUE)

# Sidebar
rounded_rect(draw, s(1036), s(84), W - s(12), s(172), s(8), NAVY, BLUE, 2)
text_centered(draw, "⚙ Sidebar Controls", s(1220), s(104), F_SUBHEAD, WHITE)
text_left(draw,  "🎭 Coach Personality (4 personas)", s(1054), s(120), F_SMALL, BLUE_MID)
text_left(draw,  "📍 Navigation  ·  📈 Quick Stats", s(1054), s(137), F_SMALL, BLUE_MID)
text_left(draw,  "✅ IBM Granite Connection Status",  s(1054), s(154), F_SMALL, BLUE_MID)

# section label tab
draw.rectangle([0, R1Y1, s(28), R1Y2], fill=hex2rgb(BLUE))
# rotated text — draw on temp surface
tmp = Image.new("RGBA", (s(112), s(28)), (0,0,0,0))
td  = ImageDraw.Draw(tmp)
text_centered(td, "USER INTERFACE", s(56), s(14), F_BADGE, WHITE)
rotated = tmp.rotate(90, expand=True)
img.paste(rotated, (0, R1Y1 + (R1Y2-R1Y1-rotated.height)//2), mask=rotated)

# ── Arrow between rows ──────────────────────────────────────────
def arrow_down(y1, y2, color=SLATE):
    cx = W // 2
    draw.line([cx, y1, cx, y2 - s(8)], fill=hex2rgb(color), width=s(2))
    draw.polygon([(cx - s(6), y2 - s(8)), (cx + s(6), y2 - s(8)), (cx, y2)], fill=hex2rgb(color))

arrow_down(R1Y2, s(196))

# ── Row 2 — Input Guardrails (y 196..268) ───────────────────────
R2Y1, R2Y2 = s(196), s(268)
rounded_rect(draw, s(36), R2Y1, W - s(12), R2Y2, s(8), PURPLE_L, PURPLE_M, 2)
rounded_rect(draw, s(56), s(208), s(224), s(256), s(7), PURPLE, "#6d28d9", 2)
text_centered(draw, "🛡 Input Guardrails", s(140), s(227), F_SUBHEAD, WHITE)
text_centered(draw, "guardrails.py", s(140), s(244), F_SMALL, "#ede9fe")

boxes2 = [
    (s(232), "Prompt Injection", "Detection & Block", "Jailbreak Detection"),
    (s(390), "PII Detection", "Email · Phone · SSN", "Redaction & Masking"),
    (s(548), "Input Validation", "Length · Format · Type", "SQL Injection Prevent"),
    (s(706), "Content Filter", "Inappropriate Content", "Malicious Input Block"),
    (s(864), "Rate Limiting", "Token Budget Check", "Max 1000 tokens/call"),
]
for bx, h, l1, l2 in boxes2:
    rounded_rect(draw, bx, s(208), bx + s(144), s(256), s(6), WHITE, PURPLE_M, 1)
    text_centered(draw, h,  bx + s(72), s(221), F_SMALL, PURPLE)
    text_centered(draw, l1, bx + s(72), s(236), F_TINY, SLATE)
    text_centered(draw, l2, bx + s(72), s(250), F_TINY, MID)

rounded_rect(draw, s(1022), s(208), W - s(12), s(256), s(6), "#faf5ff", PURPLE_M, 1)
text_centered(draw, "Session & Security Guardrails", s(1222), s(221), F_SMALL, PURPLE)
text_centered(draw, "Session ID Tracking · Credential Mgmt · API Auth · Cross-Agent Security", s(1222), s(236), F_TINY, SLATE)
text_centered(draw, "Role-Based Access · Data Privacy · Restricted Tool Execution", s(1222), s(250), F_TINY, MID)

draw.rectangle([0, R2Y1, s(28), R2Y2], fill=hex2rgb(PURPLE))
tmp2 = Image.new("RGBA", (s(72), s(28)), (0,0,0,0)); td2 = ImageDraw.Draw(tmp2)
text_centered(td2, "INPUT GUARDRAILS", s(36), s(14), F_BADGE, WHITE)
r2 = tmp2.rotate(90, expand=True); img.paste(r2, (0, R2Y1 + (R2Y2-R2Y1-r2.height)//2), mask=r2)

arrow_down(R2Y2, s(280), TEAL)

# ── Row 3 — AI Engine (y 280..448) ──────────────────────────────
R3Y1, R3Y2 = s(280), s(448)
rounded_rect(draw, s(36), R3Y1, W - s(12), R3Y2, s(8), TEAL_LIGHT, TEAL_MID, 2)

# IBM watsonx.ai block
rounded_rect(draw, s(56), s(292), s(278), s(436), s(8), NAVY, "#0ea5e9", 2)
text_centered(draw, "IBM watsonx.ai", s(167), s(314), F_HEAD, WHITE)
rounded_rect(draw, s(72), s(324), s(262), s(352), s(5), BLUE, BLUE, 0)
text_centered(draw, "ibm/granite-4-h-small", s(167), s(342), F_SMALL, WHITE)
text_centered(draw, "(Primary Model)", s(167), s(357), F_TINY, BLUE_MID)
rounded_rect(draw, s(72), s(362), s(262), s(386), s(5), SLATE, SLATE, 0)
text_centered(draw, "ibm/granite-3-1-8b-base", s(167), s(377), F_TINY, "#d1d5db")
text_centered(draw, "(Fallback Model)", s(167), s(390), F_TINY, LIGHT)
text_centered(draw, "granite_client.py", s(167), s(408), F_SMALL, "#5eead4")
text_centered(draw, "_reload_env() every render", s(167), s(422), F_TINY, "#5eead4")

# GraniteClient
rounded_rect(draw, s(292), s(292), s(464), s(436), s(8), TEAL, BORD_TEAL, 2)
text_centered(draw, "GraniteClient", s(378), s(312), F_SUBHEAD, WHITE)
text_centered(draw, "granite_client.py", s(378), s(330), F_TINY, TEAL_LIGHT)
draw.line([s(300), s(340), s(456), s(340)], fill=hex2rgb(BORD_TEAL), width=1)
for i, line in enumerate(["generate(prompt, sys)", "is_configured()", "_reload_env()", "temp · max_tokens", "load_dotenv(override=True)", "IBM_API_KEY + PROJECT_ID"]):
    text_centered(draw, line, s(378), s(354) + i * s(14), F_TINY, TEAL_LIGHT)

# Feature agents
rounded_rect(draw, s(478), s(292), W - s(12), s(448), s(8), "#f0fdfa", BORD_TEAL, 1)
text_centered(draw, "Agentic Feature Modules  —  features.py", (s(478) + W - s(12))//2, s(308), F_SUBHEAD, TEAL)
draw.line([s(478), s(318), W - s(12), s(318)], fill=hex2rgb("#99f6e4"), width=1)

agents = [
    ("Check-In\nAgent (A)", "8 context inputs\nbuild_checkin_prompt\nreadiness calc", s(496)),
    ("Workout\nAgent",      "Tailored routines\nMVW fallback\nPlan B logic",       s(606)),
    ("Meal Builder\nAgent", "Ingredients input\nIndian cuisine\nbuild_meal_prompt", s(716)),
    ("Habit Ladder\nAgent", "Steps 1→5\nConsistency gate\nbuild_habit_prompt",     s(826)),
    ("Motivation\nPersona", "4 coach styles\nSystem prompt\nbuild_system_prompt",  s(936)),
    ("Progress\nTracker",   "Active days\nAchievements\nbuild_progress_summary",   s(1046)),
    ("Readiness\nScore",    "Energy+Sleep\nSoreness+Mood\n0–100 score",            s(1156)),
    ("Plan B\nModifier",    "Easier/Harder\nNo-equip·Quiet\nLow-impact·5-min",     s(1266)),
]
for title, body, ax in agents:
    ax2 = ax + s(94)
    rounded_rect(draw, ax, s(322), ax2, s(436), s(6), WHITE, TEAL_MID, 1)
    lines = title.split("\n")
    text_centered(draw, lines[0], (ax+ax2)//2, s(336), F_TINY, TEAL)
    if len(lines) > 1:
        text_centered(draw, lines[1], (ax+ax2)//2, s(350), F_TINY, TEAL)
    draw.line([ax + s(2), s(360), ax2 - s(2), s(360)], fill=hex2rgb(TEAL_LIGHT), width=1)
    for j, bl in enumerate(body.split("\n")):
        text_centered(draw, bl, (ax+ax2)//2, s(372) + j*s(14), F_TINY, SLATE)

draw.rectangle([0, R3Y1, s(28), R3Y2], fill=hex2rgb(TEAL))
tmp3 = Image.new("RGBA", (s(168), s(28)), (0,0,0,0)); td3 = ImageDraw.Draw(tmp3)
text_centered(td3, "AI ENGINE", s(84), s(14), F_BADGE, WHITE)
r3 = tmp3.rotate(90, expand=True); img.paste(r3, (0, R3Y1 + (R3Y2-R3Y1-r3.height)//2), mask=r3)

arrow_down(R3Y2, s(460))

# ── Row 4 — Output Guardrails (y 460..532) ──────────────────────
R4Y1, R4Y2 = s(460), s(532)
rounded_rect(draw, s(36), R4Y1, W - s(12), R4Y2, s(8), PURPLE_L, PURPLE_M, 2)
rounded_rect(draw, s(56), s(472), s(224), s(520), s(7), PURPLE, "#6d28d9", 2)
text_centered(draw, "🛡 Output Guardrails", s(140), s(491), F_SUBHEAD, WHITE)
text_centered(draw, "guardrails.py", s(140), s(508), F_SMALL, "#ede9fe")

boxes4 = [
    (s(232), "Toxicity Filter",       "Harmful content block", "Medical claim redact"),
    (s(390), "Hallucination Check",   "Factual accuracy scan",  "Source confidence"),
    (s(548), "Sensitive Info Filter", "PII / Credential scrub", "Anonymization"),
    (s(706), "Format Validation",     "Response structure",     "Min/Max length"),
    (s(864), "Bias Detection",        "Ethical compliance",     "Fairness validation"),
]
for bx, h, l1, l2 in boxes4:
    rounded_rect(draw, bx, s(472), bx + s(144), s(520), s(6), WHITE, PURPLE_M, 1)
    text_centered(draw, h,  bx + s(72), s(485), F_SMALL, PURPLE)
    text_centered(draw, l1, bx + s(72), s(500), F_TINY, SLATE)
    text_centered(draw, l2, bx + s(72), s(513), F_TINY, MID)

rounded_rect(draw, s(1022), s(472), W - s(12), s(520), s(6), "#faf5ff", PURPLE_M, 1)
text_centered(draw, "Human-in-the-Loop · Multi-Agent · Ethical & Compliance Guardrails", s(1222), s(485), F_TINY, PURPLE)
text_centered(draw, "Approval workflows · Agent coordination · Audit trails · Explainability", s(1222), s(499), F_TINY, SLATE)
text_centered(draw, "Conflict resolution · Loop prevention · Responsible AI principles", s(1222), s(513), F_TINY, MID)

draw.rectangle([0, R4Y1, s(28), R4Y2], fill=hex2rgb(PURPLE))
tmp4 = Image.new("RGBA", (s(72), s(28)), (0,0,0,0)); td4 = ImageDraw.Draw(tmp4)
text_centered(td4, "OUTPUT GUARDRAILS", s(36), s(14), F_BADGE, WHITE)
r4 = tmp4.rotate(90, expand=True); img.paste(r4, (0, R4Y1 + (R4Y2-R4Y1-r4.height)//2), mask=r4)

arrow_down(R4Y2, s(544), AMBER)

# ── Row 5 — Data Layer (y 544..644) ─────────────────────────────
R5Y1, R5Y2 = s(544), s(644)
rounded_rect(draw, s(36), R5Y1, W - s(12), R5Y2, s(8), AMBER_L, AMBER_M, 2)
rounded_rect(draw, s(56), s(556), s(224), s(632), s(7), AMBER, "#92400e", 2)
text_centered(draw, "Data Layer", s(140), s(578), F_SUBHEAD, WHITE)
text_centered(draw, "progress_store.py", s(140), s(596), F_SMALL, "#fde68a")
text_centered(draw, "Local JSON · progress.json", s(140), s(612), F_TINY, "#fcd34d")

data_boxes = [
    (s(234), "Progress Store",     "record_workout()\nrecord_checkin()\nincrement_habit_day()"),
    (s(418), "Progress Fields",    "weekly_active_days\ncompleted_workouts\nhabit_streak · minutes"),
    (s(602), "Session State",      "st.session_state\ncheckin_data\nchat_history · score"),
    (s(786), "Environment",        ".env (python-dotenv)\nIBM_API_KEY\nIBM_PROJECT_ID"),
]
for bx, h, body in data_boxes:
    rounded_rect(draw, bx, s(556), bx + s(174), s(632), s(6), WHITE, AMBER_M, 1)
    text_centered(draw, h,  bx + s(87), s(572), F_SMALL, AMBER)
    for j, bl in enumerate(body.split("\n")):
        text_centered(draw, bl, bx + s(87), s(589) + j*s(14), F_TINY, SLATE)

rounded_rect(draw, s(974), s(556), W - s(12), s(632), s(6), "#fffbeb", AMBER_M, 1)
text_centered(draw, "Data Privacy & Guardrail State", s(1174), s(572), F_SMALL, AMBER)
text_centered(draw, "Data masking · Role-based access · DB access restrictions", s(1174), s(589), F_TINY, SLATE)
text_centered(draw, "guardrail_warnings log · session rate counters · token budgets", s(1174), s(603), F_TINY, SLATE)
text_centered(draw, "Unauthorized data retrieval prevention · Anonymization pipeline", s(1174), s(617), F_TINY, MID)

draw.rectangle([0, R5Y1, s(28), R5Y2], fill=hex2rgb(AMBER))
tmp5 = Image.new("RGBA", (s(100), s(28)), (0,0,0,0)); td5 = ImageDraw.Draw(tmp5)
text_centered(td5, "DATA LAYER", s(50), s(14), F_BADGE, WHITE)
r5 = tmp5.rotate(90, expand=True); img.paste(r5, (0, R5Y1 + (R5Y2-R5Y1-r5.height)//2), mask=r5)

# ── Row 6 — Security (y 656..732) ───────────────────────────────
R6Y1, R6Y2 = s(656), s(732)
rounded_rect(draw, s(36), R6Y1, W - s(12), R6Y2, s(8), RED_L, RED_M, 2)
rounded_rect(draw, s(56), s(664), s(224), s(720), s(7), RED, "#b91c1c", 2)
text_centered(draw, "Security Layer", s(140), s(685), F_SUBHEAD, WHITE)
text_centered(draw, "5 Security Guardrails", s(140), s(704), F_SMALL, "#fecaca")

sec_boxes = [
    (s(234), "Prompt Injection",  "Pattern matching",     "Jailbreak detection"),
    (s(440), "SQL Injection",     "Query sanitization",   "Parameterized queries"),
    (s(646), "Credential Mgmt",   "Secrets via .env",     "Never in source code"),
    (s(852), "Cross-Agent Sec.",  "Agent auth validate",  "Comms monitoring"),
]
for bx, h, l1, l2 in sec_boxes:
    rounded_rect(draw, bx, s(664), bx + s(192), s(720), s(6), WHITE, RED_M, 1)
    text_centered(draw, h,  bx + s(96), s(679), F_SMALL, RED)
    text_centered(draw, l1, bx + s(96), s(695), F_TINY, SLATE)
    text_centered(draw, l2, bx + s(96), s(709), F_TINY, MID)

rounded_rect(draw, s(1058), s(664), W - s(12), s(720), s(6), WHITE, RED_M, 1)
text_centered(draw, "API Authorization & Tool Execution Control", s(1268), s(679), F_SMALL, RED)
text_centered(draw, "Tool permissions matrix · Function-call validation", s(1268), s(695), F_TINY, SLATE)
text_centered(draw, "Restricted tool execution · Unauthorized action prevention", s(1268), s(709), F_TINY, MID)

draw.rectangle([0, R6Y1, s(28), R6Y2], fill=hex2rgb(RED))
tmp6 = Image.new("RGBA", (s(76), s(28)), (0,0,0,0)); td6 = ImageDraw.Draw(tmp6)
text_centered(td6, "SECURITY", s(38), s(14), F_BADGE, WHITE)
r6 = tmp6.rotate(90, expand=True); img.paste(r6, (0, R6Y1 + (R6Y2-R6Y1-r6.height)//2), mask=r6)

# ── Row 7 — Operations (y 744..860) ─────────────────────────────
R7Y1, R7Y2 = s(744), H - 4
rounded_rect(draw, s(36), R7Y1, W - s(12), R7Y2, s(8), SLATE_L, SLATE_M, 2)
rounded_rect(draw, s(56), s(752), s(224), H - s(12), s(7), SLATE, "#1f2937", 2)
text_centered(draw, "Operational", s(140), s(776), F_SUBHEAD, WHITE)
text_centered(draw, "6 Op. Guardrails", s(140), s(796), F_SMALL, "#d1d5db")
text_centered(draw, "requirements.txt", s(140), s(814), F_TINY, LIGHT)
text_centered(draw, "setup_check.py", s(140), s(830), F_TINY, LIGHT)

ops_boxes = [
    (s(234), "Execution Limits",   "Max execution time\nMax agent iterations\nRetry + failure handling"),
    (s(418), "Cost Controls",      "Token usage limits\nAPI rate limiting\nBudget monitoring"),
    (s(602), "Dependencies",       "streamlit · ibm-watson\nibm-watsonx-ai · plotly\npython-dotenv · pandas"),
    (s(786), "Testing",            "_test_guardrails.py\n23 regression tests\nAll 9 guardrail layers"),
]
for bx, h, body in ops_boxes:
    rounded_rect(draw, bx, s(752), bx + s(174), H - s(12), s(6), WHITE, SLATE_M, 1)
    text_centered(draw, h, bx + s(87), s(770), F_SMALL, SLATE)
    for j, bl in enumerate(body.split("\n")):
        text_centered(draw, bl, bx + s(87), s(788) + j*s(14), F_TINY, SLATE)

rounded_rect(draw, s(974), s(752), W - s(12), H - s(12), s(6), WHITE, SLATE_M, 1)
text_centered(draw, "Project Files", s(1208), s(770), F_SMALL, SLATE)
text_centered(draw, "app.py · granite_client.py · guardrails.py · features.py · progress_store.py", s(1208), s(788), F_TINY, SLATE)
text_centered(draw, "setup_check.py · _test_guardrails.py · requirements.txt · README.md", s(1208), s(802), F_TINY, SLATE)
text_centered(draw, ".env  (IBM_API_KEY · IBM_PROJECT_ID · IBM_GRANITE_MODEL_ID · IBM_URL)", s(1208), s(816), F_TINY, MID)
text_centered(draw, "env.example · progress.json (auto-created) · architecture_blueprint.png", s(1208), s(830), F_TINY, MID)

draw.rectangle([0, R7Y1, s(28), R7Y2], fill=hex2rgb(SLATE))
tmp7 = Image.new("RGBA", (s(100), s(28)), (0,0,0,0)); td7 = ImageDraw.Draw(tmp7)
text_centered(td7, "OPERATIONS", s(50), s(14), F_BADGE, WHITE)
r7 = tmp7.rotate(90, expand=True); img.paste(r7, (0, R7Y1 + (R7Y2-R7Y1-r7.height)//2), mask=r7)

# ── Footer legend ────────────────────────────────────────────────
legend_items = [
    (BLUE,   "User Interface (Streamlit)"),
    (PURPLE, "Guardrail Layers (9)"),
    (TEAL,   "AI Engine (IBM Granite)"),
    (AMBER,  "Data & Persistence"),
    (RED,    "Security Controls"),
    (SLATE,  "Operations & Testing"),
]
lx = s(60)
for color, label in legend_items:
    draw.rectangle([lx, H - s(16), lx + s(14), H - s(6)], fill=hex2rgb(color))
    text_left(draw, label, lx + s(18), H - s(16), F_TINY, SLATE)
    lx += s(220)

# ── Save ────────────────────────────────────────────────────────
out_path = "architecture_blueprint.png"
img.save(out_path, "PNG", optimize=True)
print(f"SUCCESS: saved {out_path}")
import os; print(f"File size: {os.path.getsize(out_path):,} bytes  |  {W}x{H}px")
