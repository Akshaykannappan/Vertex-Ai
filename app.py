"""
LEADERS DESK SKILLCAST AI — PRODUCTION SYSTEM
app.py — Complete single-file Flask API

This file contains everything:
  - Flask API server
  - Answer formatter
  - Vertex AI RAG retrieval
  - Gemini 2.5 Flash report generation
  - Error handling

HOW TO RUN:
  1. pip install flask google-cloud-aiplatform python-dotenv gunicorn
  2. Set environment variables (see .env section below)
  3. python app.py               (local testing)
  4. gunicorn app:app            (production)

ENDPOINTS:
  GET  /health    — Check if API is alive
  POST /evaluate  — Send student answers, get report JSON back
"""

import os
import re
import json
import logging
import traceback
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────
# ENVIRONMENT SETUP
# ─────────────────────────────────────────────────────────────────
load_dotenv()

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
VERTEX_CORPUS_NAME   = os.getenv("VERTEX_CORPUS_NAME", "")
LOCATION             = os.getenv("LOCATION", "us-central1")

# ─────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("skillcast")

# ─────────────────────────────────────────────────────────────────
# VERTEX AI INITIALISATION
# ─────────────────────────────────────────────────────────────────
import vertexai
from vertexai.preview import rag
from vertexai.generative_models import GenerativeModel, GenerationConfig

log.info("Connecting to Vertex AI...")
vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=LOCATION)
gemini = GenerativeModel("gemini-2.5-flash")
log.info("Vertex AI connected. Gemini 2.5 Flash loaded.")

# ─────────────────────────────────────────────────────────────────
# FLASK APP
# ─────────────────────────────────────────────────────────────────
from flask_cors import CORS
from flasgger import Swagger
app = Flask(__name__)
CORS(app)
swagger = Swagger(app, template={
    "info": {
        "title": "SkillCast AI API",
        "description": "API for evaluating student psychometric assessments",
        "version": "2.0"
    }
})


# ─────────────────────────────────────────────────────────────────
# PART 1 — FORMAT STUDENT ANSWERS INTO READABLE TEXT
# ─────────────────────────────────────────────────────────────────
def format_answers(data: dict) -> str:
    """
    Converts the student JSON from the software team into
    a clean readable text block that Gemini can analyse.
    """
    out = []

    out.append("STUDENT PSYCHOMETRIC ASSESSMENT")
    out.append("=" * 50)
    out.append(f"Name   : {data.get('name', 'Student')}")
    out.append(f"School : {data.get('school', '')}")
    out.append(f"Group  : {data.get('group', '')}")
    out.append(f"Year   : {data.get('year', '2025-26')}") 

    # Section 1 — Ambition
    out.append("\nAMBITION AND GOALS")
    ambition = data.get("ambition_specify", "") or data.get("ambition", "")
    if ambition and ambition.lower() not in ("no", "nil", ""):
        out.append(f"  Ambition : {ambition}")
    else:
        out.append(f"  Ambition : Not specified")
    out.append(f"  Can achieve it : {data.get('can_achieve', 'Not answered')}")
    out.append(f"  Strength       : {data.get('strength', 'Not specified')}")
    out.append(f"  Weakness       : {data.get('weakness', 'Not specified')}")

    # Section 2 — Subjects and interests
    out.append("\nSUBJECTS AND INTERESTS")
    subjects_liked = data.get("subjects_liked", [])
    if subjects_liked:
        out.append(f"  Subjects liked    : {', '.join(subjects_liked)}")
    subjects_disliked = data.get("subjects_disliked", [])
    if subjects_disliked:
        out.append(f"  Subjects disliked : {', '.join(subjects_disliked)}")
    interests = data.get("interests", [])
    if interests:
        out.append(f"  Interests         : {', '.join(interests)}")
    passion = data.get("passion", "")
    if passion:
        out.append(f"  Passion           : {passion}")
    learn = data.get("learn", [])
    if learn:
        out.append(f"  Wants to learn    : {', '.join(learn)}")
    score = data.get("subject_score", "")
    level = data.get("subject_level", "")
    if score:
        out.append(f"  Subject score     : {score}/100 — {level}")

    # Section 3 — Personality
    out.append("\nPERSONALITY")
    chars = [data.get("char_a",""), data.get("char_b",""), data.get("char_c","")]
    chars = [c for c in chars if c]
    if chars:
        out.append(f"  Positive traits : {', '.join(chars)}")
    if data.get("proud_of"):
        out.append(f"  Most proud of   : {data.get('proud_of')}")
    if data.get("inspires"):
        out.append(f"  Inspired by     : {data.get('inspires')}")
    out.append(f"  Can organise self   : {data.get('organise', 'Not answered')}")
    out.append(f"  Comfortable study   : {data.get('study_time', 'Not answered')}")
    out.append(f"  Likes to be alone   : {data.get('alone', 'Not answered')}")
    out.append(f"  Likes repairing     : {data.get('repair', 'Not answered')}")
    out.append(f"  Considers others    : {data.get('considers_others', 'Not answered')}")
    out.append(f"  Adjusts to others   : {data.get('adjusts', 'Not answered')}")
    stage = data.get("stage_feeling", [])
    if stage:
        out.append(f"  Feeling on stage    : {', '.join(stage)}")

    # Section 4 — Abilities, Opinions, Values
    out.append("\nABILITIES, OPINIONS AND VALUES")
    abilities = data.get("abilities", [])
    if abilities:
        out.append("  Abilities:")
        for a in abilities:
            out.append(f"    - {a}")
    opinions = data.get("opinions", [])
    if opinions:
        out.append("  Opinions of self:")
        for o in opinions:
            out.append(f"    - {o}")
    values = data.get("values", [])
    if values:
        out.append("  Values:")
        for v in values:
            out.append(f"    - {v}")

    # Section 5 — Occupation preferences
    out.append("\nOCCUPATION PREFERENCES")
    occ_map = {
        "Analytical":   data.get("occ_analytical", []),
        "Pragmatic":    data.get("occ_pragmatic", []),
        "Social":       data.get("occ_social", []),
        "Creative":     data.get("occ_creative", []),
        "Enterprising": data.get("occ_enterprising", []),
        "Conventional": data.get("occ_conventional", []),
    }
    for category, items in occ_map.items():
        if items:
            out.append(f"  {category} : {', '.join(items)}")

    # Section 6 — Life skills
    life = data.get("life_skills", {})
    if life:
        out.append("\nLIFE SKILLS")
        labels = {
            "q1_confident":   "Confident about abilities",
            "q2_introduce":   "Introduces to new people",
            "q3_listener":    "Good listener",
            "q4_ask_help":    "Asks for help",
            "q5_suggestions": "Accepts suggestions",
            "q6_trust":       "Trusts people",
            "q7_concentrate": "Difficulty concentrating",
            "q8_decisions":   "Difficulty with decisions",
            "q9_positive":    "Cannot think positively",
            "q10_say_no":     "Can say NO to others",
        }
        for key, label in labels.items():
            val = life.get(key, "")
            if val:
                out.append(f"  {label} : {val}")

    # Section 7 — Cognitive
    cog = data.get("cognitive", {})
    if cog:
        out.append("\nCOGNITIVE ANALYSIS")
        cog_labels = {
            "subjects_preferred": "Subjects preferred",
            "punctuality":        "Punctuality behaviour",
            "movie_focus":        "Movie focus",
            "maths_comfort":      "Maths comfort area",
            "project_approach":   "Project approach",
            "memory_type":        "Memory type (face/name)",
            "new_device":         "New device approach",
            "thumb_dominance":    "Thumb dominance",
            "dream_recall":       "Dream recall",
            "pencil_direction":   "Pencil direction test",
            "problem_solving":    "Problem solving style",
            "door_decision":      "Door decision",
            "restaurant_habit":   "Restaurant habit",
            "graph_preference":   "Graph preference",
            "pear_answer":        "Pear price answer",
        }
        for key, label in cog_labels.items():
            val = cog.get(key, "")
            if val:
                out.append(f"  {label} : {val}")

    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────
# PART 2 — RETRIEVE FROM VERTEX AI RAG CORPUS
# ─────────────────────────────────────────────────────────────────
def retrieve_from_corpus(query: str) -> str:
    """
    Searches the Vertex AI RAG corpus for career guidance data
    most relevant to this student profile.
    Returns the retrieved text as a string.
    Falls back to empty string if retrieval fails.
    """
    if not VERTEX_CORPUS_NAME:
        log.warning("VERTEX_CORPUS_NAME not set. Skipping RAG retrieval.")
        return ""

    try:
        log.info("Querying Vertex AI RAG corpus...")
        rag_config = rag.RagRetrievalConfig(
            top_k=6,
            ranking=rag.Ranking(
                rank_service=rag.RankService(
                    model_name="semantic-ranker-512@latest"
                )
            )
        )
        response = rag.retrieval_query(
            rag_resources=[rag.RagResource(rag_corpus=VERTEX_CORPUS_NAME)],
            text=query,
            rag_retrieval_config=rag_config,
        )
        chunks = [
            c.text.strip()
            for c in response.contexts.contexts
            if c.text.strip()
        ]
        log.info(f"Retrieved {len(chunks)} chunks from corpus.")
        return "\n\n".join(chunks)
    except Exception as e:
        log.error(f"RAG retrieval error: {e}")
        return ""


# ─────────────────────────────────────────────────────────────────
# PART 3 — BUILD PROMPT FOR GEMINI
# ─────────────────────────────────────────────────────────────────
def build_prompt(formatted_answers: str, context: str) -> str:
    """
    Builds the complete Gemini prompt.
    Includes student answers, knowledge base context,
    and the exact JSON output structure required.
    """
    context_section = ""
    if context:
        context_section = f"""
REFERENCE DATA FROM KNOWLEDGE BASE
(Similar student profiles evaluated by counsellors — use as guidance)
{"-" * 60}
{context}
{"-" * 60}
"""

    return f"""You are a senior psychometric evaluator and career guidance counsellor
at Leaders Desk Private Limited, Coimbatore, Tamil Nadu.

Your job is to evaluate a student's complete psychometric assessment
and generate a professional Skill Cast Report in the exact style of
Leaders Desk reports.
{context_section}
STUDENT ASSESSMENT ANSWERS:
{formatted_answers}

EVALUATION GUIDELINES:

1. SKILLS — evaluate each based on answers:
   - Reasoning  : logical thinking from diagram answers and cognitive style
   - Numerical  : maths comfort, number-handling, pear price answer
   - Scientific : science subject preference, awareness of biology/chemistry/physics
   - Spatial    : diagram pattern answers, 2D/3D thinking
   - System     : concentration, speed/accuracy, record-keeping ability
   - Verbal     : English preference, communication confidence

2. PERSONALITY (RIASEC model):
   - Realistic     : hands-on, mechanical, athletic preferences
   - Investigative : research, scientific, root-cause thinking
   - Artistic      : creative, imaginative, flexible thinking
   - Social        : helping, teaching, counselling preference
   - Enterprising  : leadership, persuasion, business drive
   - Conventional  : orderly, systematic, rule-following preference

3. OVERALL ANALYSIS:
   - Categorise areas as High / Moderate / Low interest
   - Based on occupation preferences, abilities, values together

4. RECOMMENDATIONS:
   - 3 to 4 specific course recommendations
   - Based on subjects, ambition, occupation interest, group
   - Use real course names (BSc Nursing, BTech CSE, BCA, etc.)
   - Reference similar profiles from knowledge base

IMPORTANT RULES:
- Write in third person consistently (He / She / They)
- Be specific to THIS student's actual answers
- Never write generic text that could apply to any student
- Match the professional tone of Leaders Desk reports
- For personality, start each section with the student's name

RETURN ONLY VALID JSON — NO extra text, NO markdown, NO code blocks.
Use exactly this structure:

{{
  "student_name": "student name here",
  "school": "school name here",
  "group": "academic group here",
  "year": "academic year here",
  "introduction": "3 to 4 sentences. Name, group, ambition, key interests, and purpose of assessment. Specific to their answers — mention their actual ambition and strongest abilities.",
  "skills": {{
    "reasoning": [
      "Specific observation about reasoning based on their diagrammatic Q answers and cognitive problem-solving style.",
      "How this reasoning ability directly connects to their recommended career path."
    ],
    "numerical": [
      "Specific observation about numerical ability from their maths comfort area and pear price answer.",
      "How this numerical skill is relevant or limiting for their recommended course."
    ],
    "scientific": [
      "Observation about scientific awareness based on their specific subject preferences.",
      "How this connects to their recommended course field.",
      "One real-world application statement linking science ability to the course."
    ],
    "spatial": [
      "Observation about spatial ability from diagram patterns and Set A/B answer.",
      "How spatial thinking aligns or does not align with their recommended career."
    ],
    "system": [
      "Observation about systematic thinking from project approach and concentration answers.",
      "How this level of systematic ability supports their recommended course path."
    ],
    "verbal": [
      "Observation about verbal ability from subject preferences and stage feeling.",
      "How verbal skills will matter specifically in their recommended career."
    ]
  }},
  "personality": {{
    "intro": "2 sentences. How this student's personality type aligns with the recommended career direction.",
    "realistic": "3 to 4 sentences. Start with student name. Connect to tools/repair answers and any pragmatic occupation choices. Link to recommendation.",
    "investigative": "3 to 4 sentences. Cover research/analysis interest based on their cognitive and occupation answers. Connect to recommended course.",
    "artistic": "3 to 4 sentences. Cover creative expression based on artistic ability and creative occupation choices. Connect to recommendation.",
    "social": "3 to 4 sentences. Cover helping/teaching tendency from life skills and occupation choices. Connect to recommendation.",
    "enterprising": "3 to 4 sentences. Cover leadership/persuasion drive from leading ability and enterprising occupation choices. Connect to recommendation.",
    "conventional": "3 to 4 sentences. Cover structure/systematic preference from record-keeping ability and conventional occupation choices. Connect to recommendation."
  }},
  "overall_analysis": {{
    "high_interest": ["Specific area 1", "Specific area 2", "Specific area 3"],
    "moderate_interest": ["Specific area 1", "Specific area 2"],
    "low_interest": ["Specific area 1", "Specific area 2"]
  }},
  "recommendations": [
    "Course 1 name — specific reason tied to this student's abilities and values",
    "Course 2 name — specific reason tied to this student's occupation interests",
    "Course 3 name — specific reason tied to this student's subjects and ambition",
    "Course 4 name — specific reason tied to overall profile alignment"
  ],
  "conclusion": "3 to 4 sentences. Summarise the student's strongest alignment between abilities, values, and recommended courses. Give a specific, encouraging closing statement about their career path that references their actual ambition and abilities — not generic motivational text."
}}"""


# ─────────────────────────────────────────────────────────────────
# PART 4 — CALL GEMINI AND PARSE RESPONSE
# ─────────────────────────────────────────────────────────────────
def call_gemini(prompt: str) -> dict:
    """
    Sends the prompt to Gemini 2.5 Flash and parses the JSON response.
    Retries once if the first attempt fails.
    Returns result dict.
    """
    gen_config = GenerationConfig(
        temperature=0.3,
        top_p=0.85,
        max_output_tokens=8192,
    )

    for attempt in range(1, 3):
        try:
            log.info(f"Calling Gemini 2.5 Flash (attempt {attempt})...")
            response = gemini.generate_content(prompt, generation_config=gen_config)
            raw = response.text.strip()

            log.info(f"Gemini responded ({len(raw)} chars). Parsing JSON...")

            # Clean response — remove markdown code fences if present
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
            raw = re.sub(r"\s*```\s*$",        "", raw, flags=re.MULTILINE)
            raw = raw.strip()

            # Find JSON boundaries
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start == -1 or end <= 1:
                raise ValueError(
                    f"No JSON object found in Gemini response. Preview: {raw[:200]}"
                )

            json_str = raw[start:end]

            # Remove control characters that break JSON
            json_str = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", json_str)

            result = json.loads(json_str)
            log.info("JSON parsed successfully.")
            return result

        except json.JSONDecodeError as e:
            log.error(f"JSON parse error on attempt {attempt}: {e}")
            if attempt == 2:
                raise ValueError(
                    f"Gemini returned invalid JSON after 2 attempts. "
                    f"Parse error: {e}. "
                    f"Response preview: {raw[:300] if 'raw' in dir() else 'no response'}"
                )
        except Exception as e:
            log.error(f"Gemini call error on attempt {attempt}: {e}")
            if attempt == 2:
                raise

    raise ValueError("Failed to get valid response from Gemini after 2 attempts.")


# ─────────────────────────────────────────────────────────────────
# PART 5 — MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────
def generate_report(student_data: dict) -> dict:
    """
    Full pipeline:
      1. Format student answers to readable text
      2. Retrieve relevant context from Vertex AI corpus
      3. Build prompt
      4. Call Gemini 2.5 Flash
      5. Return structured report dict
    """
    # Step 1
    formatted = format_answers(student_data)
    log.info("Answers formatted.")

    # Step 2
    context = retrieve_from_corpus(formatted)

    # Step 3
    prompt = build_prompt(formatted, context)

    # Step 4
    report = call_gemini(prompt)

    # Step 5
    return {"report": report}


# ─────────────────────────────────────────────────────────────────
# FLASK ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Redirect root to the Swagger API UI."""
    from flask import redirect
    return redirect("/apidocs/")


@app.route("/health", methods=["GET"])
def health():
    """
    Health check — call this to confirm API is running.
    ---
    responses:
      200:
        description: API health status returned successfully.
    """
    return jsonify({
        "status":  "running",
        "service": "SkillCast AI API — Leaders Desk",
        "model":   "gemini-2.5-flash",
        "version": "2.0",
    })


@app.route("/evaluate", methods=["POST"])
def evaluate():
    """
    Main endpoint for parsing student answers and generating a skill cast report.
    ---
    parameters:
      - in: body
        name: body
        description: Student assessment answers as JSON
        required: true
        schema:
          type: object
          properties:
            student_id:
              type: string
              example: "12345"
            name:
              type: string
              example: "Student Name"
    responses:
      200:
        description: Successfully generated the Skill Cast Report
      400:
        description: Bad request, missing or invalid JSON
      500:
        description: Internal Server Error
    """
    try:
        data = request.get_json(force=True, silent=True)

        if not data:
            return jsonify({
                "status":  "error",
                "message": "Request body is empty or not valid JSON.",
                "hint":    "Send Content-Type: application/json with student answers in the body.",
            }), 400

        student_id   = data.get("student_id", "UNKNOWN")
        student_name = data.get("name", "Student")
        log.info(f"New request — student_id: {student_id}, name: {student_name}")

        result = generate_report(data)

        log.info(f"Report complete for {student_id}.")
        return jsonify({
            "status":     "success",
            "student_id": student_id,
            "report":     result["report"],
        })

    except ValueError as ve:
        log.error(f"ValueError: {ve}")
        return jsonify({
            "status":  "error",
            "message": str(ve),
            "hint":    "This usually means Gemini returned an unexpected format. Try the request again.",
        }), 500

    except Exception as e:
        log.error(f"Unexpected error: {e}")
        traceback.print_exc()
        return jsonify({
            "status":  "error",
            "message": f"Unexpected error: {str(e)}",
        }), 500


# ─────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info("Starting SkillCast AI API on port 5005...")
    app.run(debug=False, host="0.0.0.0", port=5005)