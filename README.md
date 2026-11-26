# Agora — Personal Knowledge & Learning Companion

Agora is an AI-powered educational chatbot designed to explain Philosophy, General Knowledge, Science, World History, Mythology, Religion & Spirituality, Psychology, and **Communication, Negotiation & Professional Skills** in clear, everyday English.

## Quick Start (Zero Extra Packages Needed)

1. **Set your Gemini API key** (in your terminal or in a `.env` file copied from `.env.example`):
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```
2. **Start the backend server**:
   ```bash
   python3 server.py
   ```
3. **Open Agora in your browser**:
   Visit `http://127.0.0.1:8000`

## Modules & Features

### 1. Daily Knowledge Roulette
- 6 Balanced Slices: **Philosophy**, **Mythology**, **Science**, **English Vocabulary**, **World History**, **Health Facts**.
- Daily Official Spin + Practice Spins recorded in SQLite (`agora.db`).

### 2. Communication, Negotiation & Professional Skills Module
Integrated under **English Vocabulary**, this module teaches 30 high-impact topics:
- **Negotiation Tactics (10 Topics):** The Lowball, The Walk-Away, Bracketing, The Nibble, The Vise, Trading Concessions, BATNA, ZOPA, The Ackerman Model, The No-Oriented Question.
- **Related Communication Skills (20 Topics):** Active Listening, Assertive Communication, Persuasive Communication, Emotional Intelligence, Conflict Resolution, Handling Difficult Conversations, Asking Powerful Questions, Body Language & Non-Verbal Communication, Building Rapport, Public Speaking, Storytelling Skills, Critical Thinking in Conversations, Professional Etiquette, Giving and Receiving Feedback, Handling Rejection, Thinking Before Responding, Saying No Without Feeling Guilty, Communicating with Confidence, Interview Communication Skills, Client Communication & Relationship Management.
- **Mandatory 11-Part Lesson Structure:**
  1. Introduction
  2. Simple Explanation
  3. Background & Origin
  4. Detailed Explanation
  5. Real-Life Examples (College, Interviews/Salary, Workplace, Business/Clients, Everyday)
  6. Practical Conversation
  7. Vocabulary Builder (At least 5 words with pronunciation, meaning, origin, synonyms/antonyms, 5 sentences, natural usage guide)
  8. Common Mistakes
  9. Practical Exercise (Interactive scenario with self-attempt before ideal response)
  10. Understanding Test (Three comprehension questions)
  11. Weekly Challenge (Real-world action item)
- **Ethical Learning Philosophy:** Focuses on becoming a confident, thoughtful, ethical communicator who understands human psychology, listens carefully, and negotiates fairly for mutual benefit (win-win) rather than manipulation.

## Deploying to Vercel (1-Click Ready)

Agora is configured for serverless deployment on Vercel:

1. Import your GitHub repository (`pushparani7/agora_app`) into [Vercel](https://vercel.com).
2. In the Vercel project settings, add your **Environment Variable**:
   - `GEMINI_API_KEY`: Your Google Gemini API Key.
3. Click **Deploy**. Vercel will automatically serve the static frontend from `public/` and route `/api/*` to the Python serverless function at `api/index.py`.

## Architecture

- `api/index.py` — Vercel-native serverless Python handler that routes API requests and mounts SQLite in `/tmp` with pre-seeded topics.
- `vercel.json` — Route rewrite configuration for Vercel serverless functions and frontend static assets.
- `server.py` — Local standalone Python 3 backend (`http.server` + `urllib.request` + `sqlite3`) that persists `roulette_lessons` and `learning_topics`, applies the 11-part lesson prompt structure, and serves `/api/learning-topics`, `/api/roulette/spin`, `/api/roulette/history`, and `/api/chat`.
- `public/index.html` — Responsive frontend with **AI Companion (LLM)** mode, **Daily Roulette** with interactive wheel and Communication Module dashboard, filters, topic review, and interactive follow-ups ("Practice Exercise", "Test My Understanding").
