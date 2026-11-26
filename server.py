#!/usr/bin/env python3
"""
Agora — Personal Knowledge & Learning Companion Backend
Zero-dependency Python 3 server using standard library (http.server + urllib + sqlite3).
Keeps GEMINI_API_KEY secure on the server, manages conversation context,
and persists Daily Knowledge Roulette lessons and the Communication & Negotiation
learning database in SQLite (agora.db).
"""

import json
import os
import random
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
ENV_FILE = BASE_DIR / ".env"
DB_PATH = BASE_DIR / "agora.db"

MAX_HISTORY_TURNS = 16
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

ROULETTE_CATEGORIES = [
    "Philosophy",
    "Mythology",
    "Science",
    "English Vocabulary",
    "World History",
    "Health Facts",
]

COMMUNICATION_MODULE_TOPICS = [
    # 1. Negotiation Tactics – Complete Learning Series (10 Topics)
    {
        "module": "Negotiation Tactics",
        "topic": "The Lowball",
        "description": "Understanding low initial offers and how to respond without losing your negotiating position.",
    },
    {
        "module": "Negotiation Tactics",
        "topic": "The Walk-Away",
        "description": "Knowing when to leave a negotiation politely and protect your interests.",
    },
    {
        "module": "Negotiation Tactics",
        "topic": "Bracketing",
        "description": "Keeping your target price in the middle while negotiating.",
    },
    {
        "module": "Negotiation Tactics",
        "topic": "The Nibble",
        "description": "Recognising small additional demands and handling them professionally.",
    },
    {
        "module": "Negotiation Tactics",
        "topic": "The Vise",
        "description": "Responding to pressure such as 'You\\'ll have to do better than that.'",
    },
    {
        "module": "Negotiation Tactics",
        "topic": "Trading Concessions",
        "description": "Making progressively smaller concessions instead of giving everything away.",
    },
    {
        "module": "Negotiation Tactics",
        "topic": "BATNA (Best Alternative to a Negotiated Agreement)",
        "description": "Understanding your best alternative when an agreement cannot be reached.",
    },
    {
        "module": "Negotiation Tactics",
        "topic": "ZOPA (Zone of Possible Agreement)",
        "description": "Identifying the range in which both parties can reach an agreement.",
    },
    {
        "module": "Negotiation Tactics",
        "topic": "The Ackerman Model",
        "description": "Understanding a structured negotiation strategy involving calculated offers and counteroffers.",
    },
    {
        "module": "Negotiation Tactics",
        "topic": "The No-Oriented Question",
        "description": "Using questions that make people comfortable expressing disagreement and explaining their position.",
    },
    # 2. Related Communication Skills (20 Topics)
    {
        "module": "Communication Skills",
        "topic": "Active Listening",
        "description": "Listening to understand rather than just waiting to speak, using verbal and non-verbal cues.",
    },
    {
        "module": "Communication Skills",
        "topic": "Assertive Communication",
        "description": "Expressing needs, boundaries, and opinions clearly and respectfully without being aggressive or passive.",
    },
    {
        "module": "Communication Skills",
        "topic": "Persuasive Communication",
        "description": "Structuring arguments using logic, emotion, and credibility (Ethos, Pathos, Logos) to influence others ethically.",
    },
    {
        "module": "Communication Skills",
        "topic": "Emotional Intelligence",
        "description": "Recognizing, understanding, and managing emotions in yourself and during interactions with others.",
    },
    {
        "module": "Communication Skills",
        "topic": "Conflict Resolution",
        "description": "De-escalating tension and resolving disagreements by focusing on shared interests rather than entrenched positions.",
    },
    {
        "module": "Communication Skills",
        "topic": "Handling Difficult Conversations",
        "description": "Navigating high-stakes, sensitive, or uncomfortable discussions with composure, empathy, and clarity.",
    },
    {
        "module": "Communication Skills",
        "topic": "Asking Powerful Questions",
        "description": "Formulating open-ended, insightful questions that uncover hidden motivations and provoke thoughtful dialogue.",
    },
    {
        "module": "Communication Skills",
        "topic": "Body Language and Non-Verbal Communication",
        "description": "Mastering posture, eye contact, gestures, tone of voice, and micro-expressions to convey warmth and authority.",
    },
    {
        "module": "Communication Skills",
        "topic": "Building Rapport",
        "description": "Establishing genuine trust, common ground, and positive emotional connection quickly and authentically.",
    },
    {
        "module": "Communication Skills",
        "topic": "Public Speaking",
        "description": "Overcoming stage anxiety, organizing spoken presentations, and engaging audiences with poise.",
    },
    {
        "module": "Communication Skills",
        "topic": "Storytelling Skills",
        "description": "Using narrative arcs, relatable characters, and vivid imagery to make complex ideas memorable and engaging.",
    },
    {
        "module": "Communication Skills",
        "topic": "Critical Thinking in Conversations",
        "description": "Evaluating arguments objectively, detecting logical fallacies, and questioning assumptions without being combative.",
    },
    {
        "module": "Communication Skills",
        "topic": "Professional Etiquette",
        "description": "Mastering executive communication, meeting decorum, email clarity, and workplace professionalism.",
    },
    {
        "module": "Communication Skills",
        "topic": "Giving and Receiving Feedback",
        "description": "Delivering constructive feedback with psychological safety and receiving critique without becoming defensive.",
    },
    {
        "module": "Communication Skills",
        "topic": "Handling Rejection",
        "description": "Responding to 'no' with grace, resilience, and curiosity, maintaining relationships for future opportunities.",
    },
    {
        "module": "Communication Skills",
        "topic": "Thinking Before Responding",
        "description": "Developing the habit of deliberate pausing, emotional self-regulation, and composing thoughtful replies under pressure.",
    },
    {
        "module": "Communication Skills",
        "topic": "Saying No Without Feeling Guilty",
        "description": "Setting firm personal and professional boundaries gracefully, clearly, and without over-apologizing.",
    },
    {
        "module": "Communication Skills",
        "topic": "Communicating with Confidence",
        "description": "Projecting self-assurance, vocal variety, clear articulation, and presence in high-stakes environments.",
    },
    {
        "module": "Communication Skills",
        "topic": "Interview Communication Skills",
        "description": "Framing career narratives, handling behavioral questions (STAR method), and establishing rapport with interviewers.",
    },
    {
        "module": "Communication Skills",
        "topic": "Client Communication and Relationship Management",
        "description": "Managing expectations, communicating progress transparently, handling scope disputes, and nurturing long-term client trust.",
    },
]

AGORA_SYSTEM_PROMPT = """You are Agora, an intelligent personal knowledge and learning companion.
Your purpose is to help curious learners understand the world, human existence, scientific discoveries, civilizations, cultures, religions, mythology, psychology, and mastery of English communication and negotiation.

SUBJECTS YOU COVER:
- Philosophy (Ancient Greek, Indian, Western, existentialism, nihilism, Stoicism, ethics, consciousness, meaning, identity, freedom, happiness).
- General Knowledge (geography, world organizations, political systems, inventions, economics, society).
- Science (physics, chemistry, biology, space/astronomy, evolution, genetics/DNA, AI/technology, natural phenomena, climate).
- World History (ancient civilizations like Egypt, Greece, Rome, Mesopotamia, Indian history, empires, revolutions, world wars, how modern societies developed).
- Mythology (Greek, Roman, Hindu, Norse, Egyptian, and other traditions—tell stories engagingly while distinguishing myth from verified history).
- Religion, God & Spirituality (Hinduism, Christianity, Islam, Buddhism, Jainism, Sikhism, creation stories, theism/atheism/agnosticism, science and religion). Always treat religious subjects respectfully: distinguish religious beliefs, philosophical interpretations, historical evidence, and scientific facts. Never present one religion's beliefs as universally established facts.
- Psychology & Human Behaviour (emotions, cognitive biases, memory, perception, social psychology, habits, decision-making).
- English Vocabulary, Communication & Negotiation (English fluency, advanced vocabulary in context, negotiation tactics, interpersonal communication, conflict resolution, active listening, assertive speaking, ethical negotiation for mutual benefit, professional etiquette, client and interview communication).

EXPLANATION STYLE (CRITICAL):
1. Start with the simplest possible explanation in natural, everyday English.
2. Explain unfamiliar words immediately in plain language.
3. Break complicated subjects into short, readable sections with clear headings or bullet points.
4. Use relatable everyday examples.
5. Explain WHY something happens, not just WHAT happens.
6. Provide historical context when helpful.
7. Connect different subjects whenever meaningful.
8. Never assume the user already knows the basics; avoid unnecessary academic jargon or dry textbook answers.

COMMUNICATION & NEGOTIATION TEACHING PHILOSOPHY:
- Emphasize ethical, thoughtful communication and mutual benefit (win-win) rather than dishonest manipulation or cheap tricks.
- The goal is to develop a confident, thoughtful communicator who understands human psychology, listens attentively, articulates points with conviction, and resolves disagreements with poise.
- When the user asks follow-up questions, simplify explanations when requested ("Explain Like I'm a Beginner"), provide supportive, precise feedback on their attempts at practical exercises, and gradually challenge them with deeper nuances.

ACCURACY & PERSONALITY:
- Use conversation history naturally for follow-up questions.
- Never invent historical facts, scientific studies, or quotations. Acknowledge uncertainty when historians or scientists disagree.
- Personality: thoughtful, intellectually curious, patient, warm, and engaging."""


def load_dotenv():
    """Load key=value pairs from .env if present."""
    if not ENV_FILE.exists():
        return
    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS roulette_lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spin_date TEXT NOT NULL,
                is_official INTEGER NOT NULL DEFAULT 1,
                category TEXT NOT NULL,
                topic TEXT NOT NULL,
                article TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL DEFAULT 'English Vocabulary',
                module TEXT NOT NULL,
                topic TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'uncompleted',
                completed_at TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        now = datetime.now().isoformat()
        for item in COMMUNICATION_MODULE_TOPICS:
            conn.execute(
                """
                INSERT INTO learning_topics (category, module, topic, description, status, created_at)
                VALUES ('English Vocabulary', ?, ?, ?, 'uncompleted', ?)
                ON CONFLICT(topic) DO UPDATE SET
                    description = excluded.description,
                    module = excluded.module
                """,
                (item["module"], item["topic"], item["description"], now),
            )
        # Sync completion status with previously recorded roulette lessons
        conn.execute(
            """
            UPDATE learning_topics
            SET status = 'completed', completed_at = (
                SELECT created_at FROM roulette_lessons WHERE roulette_lessons.topic = learning_topics.topic LIMIT 1
            )
            WHERE topic IN (SELECT topic FROM roulette_lessons)
            """
        )
        conn.commit()


def row_to_dict(row):
    return {
        "id": row["id"],
        "spinDate": row["spin_date"],
        "isOfficial": bool(row["is_official"]),
        "category": row["category"],
        "topic": row["topic"],
        "article": row["article"],
        "createdAt": row["created_at"],
    }


def topic_row_to_dict(row):
    return {
        "id": row["id"],
        "category": row["category"],
        "module": row["module"],
        "topic": row["topic"],
        "description": row["description"],
        "status": row["status"],
        "completedAt": row["completed_at"],
        "createdAt": row["created_at"],
    }


def trim_conversation_history(messages):
    if len(messages) <= MAX_HISTORY_TURNS:
        return messages
    trimmed = messages[-MAX_HISTORY_TURNS:]
    while trimmed and trimmed[0].get("role") != "user":
        trimmed = trimmed[1:]
    return trimmed or messages[-MAX_HISTORY_TURNS:]


def call_gemini_raw(system_prompt, contents, api_key, max_tokens=1600):
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.75,
            "maxOutputTokens": max_tokens,
            "thinkingConfig": {"thinkingBudget": 1024},
        },
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("No response candidates returned by the language model.")

    parts = candidates[0].get("content", {}).get("parts", [])
    reply_text = "".join(p.get("text", "") for p in parts).strip()
    if not reply_text:
        raise ValueError("The language model returned an empty reply.")

    return reply_text, data.get("usageMetadata", {})


def call_gemini_chat(messages, api_key):
    recent_messages = trim_conversation_history(messages)
    contents = []
    for turn in recent_messages:
        role = "model" if turn.get("role") == "assistant" else "user"
        text = str(turn.get("text", "")).strip()
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})

    reply_text, usage = call_gemini_raw(AGORA_SYSTEM_PROMPT, contents, api_key, max_tokens=4096)
    return {
        "reply": reply_text,
        "model": GEMINI_MODEL,
        "trimmed": len(messages) > MAX_HISTORY_TURNS,
        "usage": {
            "promptTokens": usage.get("promptTokenCount"),
            "responseTokens": usage.get("candidatesTokenCount"),
            "totalTokens": usage.get("totalTokenCount"),
        },
    }


def generate_roulette_lesson(category, used_topics, api_key, requested_topic=None):
    avoid_list = ", ".join(used_topics[-30:]) if used_topics else "None yet"

    # Check if this should be a Communication & Negotiation lesson under English Vocabulary
    is_comm_lesson = False
    chosen_comm_topic = None

    if category == "English Vocabulary":
        with get_db() as conn:
            if requested_topic:
                chosen_comm_topic = conn.execute(
                    "SELECT * FROM learning_topics WHERE topic = ?", (requested_topic,)
                ).fetchone()
                if chosen_comm_topic:
                    is_comm_lesson = True
            else:
                uncompleted_rows = conn.execute(
                    "SELECT * FROM learning_topics WHERE category = 'English Vocabulary' AND status = 'uncompleted'"
                ).fetchall()
                # Mix traditional vocabulary with communication & negotiation lessons
                # When uncompleted topics exist, ~70% chance of a Communication/Negotiation topic
                if uncompleted_rows and random.random() < 0.70:
                    chosen_comm_topic = random.choice(uncompleted_rows)
                    is_comm_lesson = True

    if is_comm_lesson and chosen_comm_topic:
        topic_title = chosen_comm_topic["topic"]
        module_name = chosen_comm_topic["module"]
        topic_desc = chosen_comm_topic["description"]

        prompt = f"""You are teaching a lesson in the master series: "Communication, Negotiation & Professional Skills" under the category "English Vocabulary".
TOPIC: {topic_title}
SUBMODULE: {module_name}
CORE THEME: {topic_desc}

LEARNING PHILOSOPHY (CRITICAL):
The learner does NOT want manipulative negotiation tricks or dishonest tactics.
The goal is to develop an ethical, confident, thoughtful communicator who understands human psychology and behaviour, listens carefully, expresses ideas clearly with conviction, handles disagreements and high pressure intelligently, and negotiates fairly for mutual benefit (win-win).
The long-term objective is to communicate confidently with clients, colleagues, managers, interviewers, entrepreneurs, and people from diverse backgrounds.
The goal is NOT merely learning English words; it is becoming better at using English to think, communicate, negotiate, and express oneself.

FORMAT REQUIREMENTS:
Line 1 MUST be exactly:
TOPIC: {topic_title}

Then write an exceptional, in-depth, beginner-friendly learning guide in clear, natural everyday English following this EXACT 11-part Markdown structure (do NOT omit, combine, or rename any section):

## 1. Introduction
What is this concept and why should I learn it? Explain why it is essential for modern professional and personal life.

## 2. Simple Explanation
Explain it in beginner-friendly English without unnecessarily complicated terminology or dry academic jargon. Use an intuitive, everyday analogy.

## 3. Background and Origin
Explain where the concept originated, who introduced or popularised it (e.g. Harvard Negotiation Project, Chris Voss, William Ury, Robert Cialdini, classical rhetoric, or cognitive psychology), and any interesting historical or psychological context.

## 4. Detailed Explanation
Break down how it works, its core principles, underlying psychological dynamics, and its different applications. Emphasize ethical application and mutual benefit.

## 5. Real-Life Examples
Provide 5 distinct, detailed, realistic scenarios demonstrating how this concept plays out in practice:
### A. College and Student Life (group projects, professors, campus negotiations)
### B. Job Interviews and Salary Negotiations (evaluating offers, negotiating compensation, handling curveballs)
### C. Workplace Situations (deadlines, promotions, collaborating with cross-functional teams, managing managers)
### D. Business and Client Negotiations (scope changes, pricing discussions, contract terms, managing expectations)
### E. Everyday Conversations (friends, family, rent, purchasing, setting personal boundaries)

## 6. Practical Conversation
Provide a realistic, natural dialogue illustrating how to use this concept gracefully in a high-stakes conversation. Include brief commentary on what each speaker does well.

## 7. Vocabulary Builder
Introduce at least 5 important English words connected to this topic (such as: Concession, Leverage, Counteroffer, Persuasion, Compromise, Assertiveness, Credibility, Rapport, Objection, Deliberation, Strategic, Conviction, Manipulation, Mutual benefit, Reservation price, etc.).
For EACH of the 5+ vocabulary words, provide all 6 items:
1. **Pronunciation**: Phonetic spelling and syllable breakdown.
2. **Simple English Meaning**: Clear definition in simple terms.
3. **Word Origin**: Interesting etymology and history.
4. **Synonyms and Antonyms**: At least 3 synonyms and 2 antonyms.
5. **Five Practical Example Sentences**: Ranging from casual conversation to executive professional contexts.
6. **Natural Usage Guide**: Tips on how to naturally incorporate it into everyday and professional conversations without sounding pretentious.

## 8. Common Mistakes
Explain what people usually get wrong when trying to apply this concept (e.g. confusing assertiveness with aggression, giving away concessions too early, manipulating rather than collaborating) and how to avoid these traps.

## 9. Practical Exercise
Present a realistic, challenging situation and ask the learner: "How would you respond in this situation?"
Prompt the learner to attempt their own response first before looking ahead or reading an ideal response. Provide an analysis of what an ideal, ethical response should contain.

## 10. Understanding Test
Ask three distinct, thought-provoking questions to check whether the learner genuinely understands the concept rather than just memorizing definitions.

## 11. Weekly Challenge
Give the learner one actionable, small, real-world activity to safely practice this skill in daily interactions this week to build confidence and fluency."""

    elif category == "English Vocabulary":
        # Traditional English Vocabulary Lesson
        prompt = f"""Select ONE uncommon, genuinely useful English word (not basic words like 'happy' or 'ubiquitous').
Do NOT repeat any of these previously covered topics: {avoid_list}.

FORMAT REQUIREMENTS:
Line 1 MUST be exactly:
TOPIC: Understanding "<Word>" - <Short Clear Subtitle>

Then write a substantial, engaging learning article in extremely simple, natural English for a curious beginner following this exact 9-part Markdown structure:
## 1. Topic Introduction
## 2. What Does It Mean?
Include clear phonetic pronunciation, syllable breakdown, and simple everyday meaning.
## 3. Background and Origin
Word origin and etymology.
## 4. Detailed Explanation
Nuances, synonyms, and antonyms.
## 5. Interesting Facts
How the word evolved or famous usage.
## 6. Real-Life Examples and Connections
Provide FIVE practical everyday and professional example sentences showing natural usage.
## 7. Why Is This Important?
How to use it naturally in conversation without sounding pretentious.
## 8. Three Surprising Things to Remember
## 9. Three Questions to Test Your Understanding"""

    else:
        # Standard lesson for Philosophy, Mythology, Science, World History, Health Facts
        prompt = f"""Select ONE fascinating, relatively unfamiliar, and intellectually rewarding topic in the category: "{category}".
Do NOT repeat any of these previously covered topics: {avoid_list}.

FORMAT REQUIREMENTS:
Line 1 MUST be exactly:
TOPIC: <Short clear title of the chosen topic>

Then write a substantial, engaging learning article in extremely simple, natural English for a curious beginner.
Avoid complicated jargon (and whenever you introduce a useful new English word, explain its meaning immediately).
Never invent historical facts, scientific studies, or quotes.

Use this exact 9-part Markdown structure:
## 1. Topic Introduction
## 2. What Does It Mean?
## 3. Background and Origin
## 4. Detailed Explanation
## 5. Interesting Facts
## 6. Real-Life Examples and Connections
## 7. Why Is This Important?
## 8. Three Surprising Things to Remember
## 9. Three Questions to Test Your Understanding"""

    contents = [{"role": "user", "parts": [{"text": prompt}]}]
    raw_text, _ = call_gemini_raw(AGORA_SYSTEM_PROMPT, contents, api_key, max_tokens=8192)

    lines = raw_text.splitlines()
    topic = chosen_comm_topic["topic"] if (is_comm_lesson and chosen_comm_topic) else f"Hidden Gem in {category}"
    article_lines = lines
    if lines and lines[0].strip().upper().startswith("TOPIC:"):
        topic = lines[0].split(":", 1)[1].strip() or topic
        article_lines = lines[1:]

    article = "\n".join(article_lines).strip()
    return topic, article


class AgoraHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        return json.loads(raw_body.decode("utf-8"))

    def do_GET(self):
        if self.path == "/api/health":
            api_key = os.environ.get("GEMINI_API_KEY", "").strip()
            self.send_json(
                200,
                {
                    "ok": True,
                    "hasApiKey": bool(api_key),
                    "model": GEMINI_MODEL,
                },
            )
            return

        if self.path.startswith("/api/learning-topics"):
            with get_db() as conn:
                rows = conn.execute(
                    "SELECT * FROM learning_topics ORDER BY id ASC"
                ).fetchall()
                topics = [topic_row_to_dict(r) for r in rows]
                total = len(topics)
                completed_count = sum(1 for t in topics if t["status"] == "completed")
                uncompleted_count = total - completed_count
            self.send_json(
                200,
                {
                    "total": total,
                    "completedCount": completed_count,
                    "uncompletedCount": uncompleted_count,
                    "topics": topics,
                },
            )
            return

        if self.path.startswith("/api/roulette/history"):
            today_str = datetime.now().strftime("%Y-%m-%d")
            with get_db() as conn:
                rows = conn.execute(
                    "SELECT * FROM roulette_lessons ORDER BY id DESC LIMIT 50"
                ).fetchall()
                official_row = conn.execute(
                    "SELECT * FROM roulette_lessons WHERE spin_date = ? AND is_official = 1 ORDER BY id DESC LIMIT 1",
                    (today_str,),
                ).fetchone()
            self.send_json(
                200,
                {
                    "officialToday": row_to_dict(official_row) if official_row else None,
                    "history": [row_to_dict(r) for r in rows],
                },
            )
            return

        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        if self.path == "/api/chat":
            if not api_key:
                self.send_json(
                    503,
                    {
                        "error": "API_KEY_MISSING",
                        "message": "GEMINI_API_KEY is not configured on the server. Set it in your environment or .env file and restart server.py.",
                    },
                )
                return

            try:
                body = self.read_json_body()
            except Exception:
                self.send_json(400, {"error": "Invalid JSON request body."})
                return

            messages = body.get("messages")
            if not isinstance(messages, list) or not messages:
                self.send_json(400, {"error": "messages must be a non-empty list."})
                return

            try:
                result = call_gemini_chat(messages, api_key)
                self.send_json(200, result)
            except urllib.error.HTTPError as exc:
                err_body = exc.read().decode("utf-8", errors="replace")
                self.send_json(
                    502,
                    {
                        "error": "UPSTREAM_API_ERROR",
                        "message": f"Language model API returned HTTP {exc.code}.",
                        "details": err_body[:400],
                    },
                )
            except Exception as exc:
                self.send_json(500, {"error": "SERVER_ERROR", "message": str(exc)})
            return

        if self.path == "/api/roulette/spin":
            if not api_key:
                self.send_json(
                    503,
                    {
                        "error": "API_KEY_MISSING",
                        "message": "GEMINI_API_KEY is not configured on the server.",
                    },
                )
                return

            try:
                body = self.read_json_body()
            except Exception:
                self.send_json(400, {"error": "Invalid JSON request body."})
                return

            category = str(body.get("category", "")).strip()
            if category not in ROULETTE_CATEGORIES:
                self.send_json(400, {"error": "Invalid roulette category."})
                return

            requested_topic = str(body.get("topic", "")).strip() or None
            is_official = bool(body.get("isOfficial", True))
            spin_date = str(body.get("localDate") or datetime.now().strftime("%Y-%m-%d"))[:10]

            with get_db() as conn:
                if is_official:
                    existing = conn.execute(
                        "SELECT * FROM roulette_lessons WHERE spin_date = ? AND is_official = 1 LIMIT 1",
                        (spin_date,),
                    ).fetchone()
                    if existing:
                        self.send_json(
                            409,
                            {
                                "error": "ALREADY_SPUN_TODAY",
                                "message": "Today's official daily spin has already been recorded. Use Practice Spin to explore more!",
                                "existing": row_to_dict(existing),
                            },
                        )
                        return

                prev_rows = conn.execute(
                    "SELECT topic FROM roulette_lessons WHERE category = ? ORDER BY id DESC LIMIT 30",
                    (category,),
                ).fetchall()
                used_topics = [r["topic"] for r in prev_rows]

            try:
                topic, article = generate_roulette_lesson(
                    category, used_topics, api_key, requested_topic=requested_topic
                )
                created_at = datetime.now().isoformat(timespec="seconds")
                with get_db() as conn:
                    cur = conn.execute(
                        """
                        INSERT INTO roulette_lessons (spin_date, is_official, category, topic, article, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (spin_date, 1 if is_official else 0, category, topic, article, created_at),
                    )
                    # If this topic is in learning_topics, mark it completed
                    conn.execute(
                        "UPDATE learning_topics SET status = 'completed', completed_at = ? WHERE topic = ?",
                        (created_at, topic),
                    )
                    conn.commit()
                    new_row = conn.execute(
                        "SELECT * FROM roulette_lessons WHERE id = ?", (cur.lastrowid,)
                    ).fetchone()
                self.send_json(200, {"lesson": row_to_dict(new_row)})
            except urllib.error.HTTPError as exc:
                err_body = exc.read().decode("utf-8", errors="replace")
                self.send_json(
                    502,
                    {
                        "error": "UPSTREAM_API_ERROR",
                        "message": f"Language model API returned HTTP {exc.code}.",
                        "details": err_body[:400],
                    },
                )
            except Exception as exc:
                self.send_json(500, {"error": "SERVER_ERROR", "message": str(exc)})
            return

        self.send_json(404, {"error": "Endpoint not found."})

    def log_message(self, format, *args):
        print(f"[Agora] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    load_dotenv()
    init_db()
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), AgoraHandler)
    has_key = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    print(f"Agora server running at http://127.0.0.1:{port}")
    print(f"SQLite database: {DB_PATH}")
    print(f"Gemini API key configured: {'YES' if has_key else 'NO (set GEMINI_API_KEY)'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Agora server.")
        server.server_close()
