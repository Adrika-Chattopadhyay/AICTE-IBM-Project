# Fitness Buddy 💪

**AI-Powered Health & Fitness Coach — Built with IBM Granite on watsonx.ai**

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure IBM Cloud (for live AI)
```bash
# Copy the example env file
cp env.example .env

# Edit .env and add your IBM credentials:
# IBM_API_KEY=your_actual_api_key
# IBM_PROJECT_ID=your_project_id
```

**Get IBM Cloud credentials (free tier):**
1. Sign up at [https://cloud.ibm.com](https://cloud.ibm.com)
2. Create a watsonx.ai project at [https://dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
3. Generate an API key: IBM Cloud → Manage → Access (IAM) → API Keys
4. Copy your Project ID from watsonx.ai project settings

### 3. Run the App
```bash
streamlit run app.py
```

### 4. Verify Setup (optional)
```bash
python setup_check.py
```

> **Note:** The app works in **Demo Mode** without IBM credentials — all features are available with pre-built responses. Add real IBM credentials to get fully personalized AI-generated content.

---

## ✨ Features

### A. Adaptive Daily Check-In
Before generating a plan, the app collects:
- Available time (5/10/20/30/45 min)
- Energy level, mood, sleep hours
- Workout location and available equipment
- Experience level, pain areas, soreness

### B. Minimum Viable Workout
Never returns "no workout today." Options include:
- 3-minute mobility routine
- 5-minute walking challenge
- Chair-based routine
- Breathing & stretching session
- One-round bodyweight circuit

### C. Plan B Button
Every workout includes 6 instant modifications:
- Make it easier / harder
- No-equipment alternative
- Quiet apartment version
- Low-impact version
- Shorten to 5 minutes

### D. Smart Meal Builder
Enter pantry ingredients and preferences:
- Vegetarian/non-veg/vegan/eggetarian/Jain
- Allergy filtering
- Indian regional preferences (North/South/West/East)
- Budget-conscious suggestions
- Indian staples: dal, roti, rice, paneer, eggs, poha, chana, sprouts, curd

### E. Habit Ladder
5-level progressive habit system:
1. Drink one extra glass of water
2. Walk for 5 minutes
3. Short mobility routine
4. Add a balanced breakfast
5. Follow a structured workout

Levels unlock based on consistency (not just time).

### F. Motivation Personality
4 coach styles:
- 🤗 Gentle Friend — supportive & non-judgmental
- ⚡ Energetic Coach — enthusiastic & challenge-oriented
- 🧘 Calm Guide — concise & mindful
- 🎯 Accountability Partner — direct but respectful

### G. Fitness Readiness Score
Daily score (0–100) based on:
- Energy, sleep, mood, soreness, available time, recovery

Recommends workout intensity. *Not a medical score.*

### H. Progress Beyond Weight
Tracks:
- Weekly active days
- Completed workouts & total minutes
- Habit streak & level
- Energy trends
- Achievements & milestones

---

## 🔐 Guardrails (9 Layers)

| # | Layer | What it protects |
|---|-------|-----------------|
| 1 | Input Guardrails | Prompt injection, PII, SQL injection, harmful content |
| 2 | Output Guardrails | Toxicity, hallucination risk, medical disclaimers |
| 3 | Tool Execution | API authorization, rate limiting, function validation |
| 4 | Data Guardrails | Role-based access, PII masking, query validation |
| 5 | Security | Jailbreak detection, session blocking, credential safety |
| 6 | Operational | Timeouts, daily API limits, retry with backoff |
| 7 | Human-in-the-Loop | Emergency escalation, critical action gates |
| 8 | Multi-Agent | Agent access control, loop prevention, message validation |
| 9 | Ethical & Compliance | Bias detection, fairness, audit trail, regulatory compliance |

---

## 📁 Project Structure

```
fitness-buddy/
├── app.py                  # Main Streamlit application
├── granite_client.py       # IBM Granite / watsonx.ai integration
├── guardrails.py           # All 9 guardrail layers
├── features.py             # Feature modules (A–H)
├── progress_store.py       # Progress tracking & persistence
├── setup_check.py          # Setup verification script
├── requirements.txt        # Python dependencies
├── env.example             # Environment variable template
└── README.md               # This file
```

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| AI Model | IBM Granite (ibm/granite-13b-chat-v2) |
| AI Platform | IBM watsonx.ai on IBM Cloud |
| Frontend | Streamlit |
| Charts | Plotly |
| Data | Pandas |
| Guardrails | Custom Python (9 layers) |

---

## ⚠️ Disclaimers

- This app provides general wellness guidance only — **not medical advice**
- Always consult a qualified healthcare professional before starting a new fitness program
- The Fitness Readiness Score is not a medical assessment
- Meal suggestions are not guaranteed weight-loss solutions
- **Mental health support (India):** iCall — 9152987821
- **Emergency:** 112
