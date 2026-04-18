"""
LEADERS DESK SKILLCAST AI — PRODUCTION SYSTEM
app.py — Complete single-file Flask API

This file handles:
  - Flask API server with Swagger UI
  - Keyword-dense student answer formatting (Token Optimized)
  - Vertex AI RAG retrieval
  - Gemini 2.5 Flash report generation with Industry suggestions
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
        "version": "3.0"
    }
})

# ─────────────────────────────────────────────────────────────────
# PART 1 — FORMAT STUDENT ANSWERS (KEYWORD DENSE)
# ─────────────────────────────────────────────────────────────────
def format_answers(data: dict) -> str:
    """
    Converts student JSON into a highly concise, keyword-dense text block.
    Optimized for token reduction and better RAG performance.
    """
    out = []
    
    # Header minimal
    out.append(f"Student: {data.get('name','')} | Group: {data.get('group','')}")

    # Section 1: Ambition & Goals
    out.append(f"Ambition: {data.get('q1_ambition','Unspecified')}")
    out.append(f"Confidence: {data.get('q2_can_achieve','')} | Strength: {data.get('q3_strength','')} | Weakness: {data.get('q4_weakness','')}")
    out.append(f"Performance: {data.get('q5_subjects_avg','')} | Passion: {data.get('q7_passion','')}")
    
    # Interests & Subjects
    likes = data.get("q9_likes_subjects", [])
    dislikes = data.get("q10_dislikes_subjects", [])
    out.append(f"Likes: {', '.join(likes) if likes else 'None'}")
    out.append(f"Dislikes: {', '.join(dislikes) if dislikes else 'None'}")
    
    # Traits
    traits = data.get("q11_positive_traits", [])
    out.append(f"Traits: {', '.join(traits)} | Pride: {data.get('q12_proud_of','')} | Inspiration: {data.get('q13_inspires','')}")
    out.append(f"Stage: {', '.join(data.get('q15_stage_feeling', []))}")
    
    # Habits
    out.append(f"Habits: Study({data.get('q17_study_time','')}), Alone({data.get('q18_alone_time','')}), Repair({data.get('q19_repair_things','')}), Organize({data.get('q14_organize_self','')})")
    out.append(f"Social: Considerate({data.get('q20_consider_others','')}), Adapts({data.get('q21_adjust_level','')}), Sensitivity({data.get('q22_insensitive_behavior','')})")

    # Abilities, Opinions, Values
    out.append(f"Abilities: {', '.join(data.get('abilities', []))}")
    out.append(f"Opinions: {', '.join(data.get('opinions', []))}")
    out.append(f"Values: {', '.join(data.get('values', []))}")

    # Occupation Preferences (RIASEC)
    for cat in ["analytical", "pragmatic", "social", "creative", "enterprising", "conventional"]:
        items = data.get(f"occ_{cat}", [])
        if items:
            out.append(f"{cat.capitalize()}: {', '.join(items)}")

    # Life Skills (Shortened)
    ls = data.get("life_skills", {})
    if ls:
        res = [f"{k.split('_', 1)[1] if '_' in k else k}:{v}" for k, v in ls.items() if v]
        out.append(f"LifeSkills: {', '.join(res)}")

    # Diagrammatic
    diag = data.get("diagrammatic", {})
    if diag:
        out.append(f"Reasoning: Q1({diag.get('q1','')}), Q2({diag.get('q2','')})")

    # Cognitive (Shortened)
    cog = data.get("cognitive", {})
    if cog:
        items = []
        for k, v in cog.items():
            label = k.split('_', 1)[1] if '_' in k else k
            items.append(f"{label}:{v}")
        out.append(f"Cognitive: {', '.join(items)}")

    return "\n".join(out)

# ─────────────────────────────────────────────────────────────────
# PART 2 — RETRIEVE FROM VERTEX AI RAG CORPUS
# ─────────────────────────────────────────────────────────────────
def retrieve_from_corpus(query: str) -> str:
    """
    Searches the Vertex AI RAG corpus for career guidance data.
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
        chunks = [c.text.strip() for c in response.contexts.contexts if c.text.strip()]
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
    Builds the complete Gemini prompt with Industry focus.
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
STUDENT ASSESSMENT ANSWERS (Keyword-Dense):
{formatted_answers}

EVALUATION GUIDELINES:

1. SKILLS — evaluate each based on answers:
   - Reasoning  : logical thinking from reasoning Qs and cognitive style
   - Numerical  : maths comfort, number-handling, pear price answer
   - Scientific : science subject preference, awareness
   - Spatial    : diagram pattern answers, cognitive style
   - System     : concentration, speed/accuracy, record-keeping
   - Verbal     : English preference, communication confidence

2. PERSONALITY (RIASEC model):
   - Realistic, Investigative, Artistic, Social, Enterprising, Conventional.
   - Evaluate based on habits, traits, and occupation interests.

3. OVERALL ANALYSIS:
   - Categorise areas as High / Moderate / Low interest.

4. RECOMMENDATIONS:
   - Identify 1 to 3 (minimum 1, maximum 3) Core Industry Areas for the student.
   - STICK STRICTLY to the "Industry" column values from the job opportunities data found in the REFERENCE DATA provided. Do not make up your own industry names.
   - Match industries based on student subjects, ambition, RIASEC personality, and strongest skills.

IMPORTANT RULES:
- Write in third person consistently (He / She / They)
- Be specific to THIS student's actual answers
- NEVER write generic text
- Match the professional tone of Leaders Desk
- NEVER suggest specific courses, degrees, or specific job titles (like BBA, CA, Banking, Engineering degree, etc.) in the recommendations list.
- The "recommendations" MUST be a simple list containing ONLY the exact names of the broad Core Industry Areas extracted from the reference data.

RETURN ONLY VALID JSON.
Use exactly this structure:

{{
  "student_name": "student name here",
  "school": "school name here",
  "group": "academic group here",
  "year": "academic year here",
  "introduction": "3 to 4 sentences about student profile and assessment purpose.",
  "skills": {{
    "reasoning": ["Spec observation", "How it connects to career"],
    "numerical": ["Spec observation", "How it connects to career"],
    "scientific": ["Spec observation", "How it connects to career"],
    "spatial": ["Spec observation", "How it connects to career"],
    "system": ["Spec observation", "How it connects to career"],
    "verbal": ["Spec observation", "How it connects to career"]
  }},
  "personality": {{
    "intro": "2 sentences about personality alignment.",
    "realistic": "3 to 4 sentences.",
    "investigative": "3 to 4 sentences.",
    "artistic": "3 to 4 sentences.",
    "social": "3 to 4 sentences.",
    "enterprising": "3 to 4 sentences.",
    "conventional": "3 to 4 sentences."
  }},
  "overall_analysis": {{
    "high_interest": ["area 1", "area 2"],
    "moderate_interest": ["area 1"],
    "low_interest": ["area 1"]
  }},
  "recommendations": ["Industry Name 1", "Industry Name 2"],
  "conclusion": "3 to 4 sentences summarising alignment and closing encouraging statement."
}} """

# ─────────────────────────────────────────────────────────────────
# PART 4 — CALL GEMINI AND PARSE RESPONSE
# ─────────────────────────────────────────────────────────────────
def call_gemini(prompt: str) -> dict:
    """
    Sends search query to Gemini and parses the JSON response.
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

            # Clean response
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
            raw = re.sub(r"\s*```\s*$",        "", raw, flags=re.MULTILINE)
            raw = raw.strip()

            # Find JSON boundaries
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start == -1 or end <= 1:
                raise ValueError("No JSON object found in Gemini response.")

            json_str = raw[start:end]
            json_str = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", json_str)

            result = json.loads(json_str)
            log.info("JSON parsed successfully.")
            return result

        except Exception as e:
            log.error(f"Gemini attempt {attempt} failed: {e}")
            if attempt == 2: raise

    raise ValueError("Failed to get valid response from Gemini.")

# ─────────────────────────────────────────────────────────────────
# PART 5 — MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────
def generate_report(student_data: dict) -> dict:
    # Step 1: Short-Form Formatting
    formatted = format_answers(student_data)
    log.info("Answers formatted (Short-Form).")

    # Step 2: RAG
    context = retrieve_from_corpus(formatted)

    # Step 3: Prompt
    prompt = build_prompt(formatted, context)

    # Step 4: AI
    report = call_gemini(prompt)

    return {"report": report}

# ─────────────────────────────────────────────────────────────────
# FLASK ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    from flask import redirect
    return redirect("/apidocs/")

@app.route("/health", methods=["GET"])
def health():
    """
    Health check — confirms API status.
    ---
    responses:
      200:
        description: API is alive and running correctly.
    """
    return jsonify({
        "status":  "running",
        "model":   "gemini-2.5-flash",
        "version": "3.0",
    })

@app.route("/evaluate", methods=["POST"])
def evaluate():
    """
    Generate SkillCast Report from student answers.
    ---
    parameters:
      - in: body
        name: body
        description: Student answers (Keyword-Dense Format)
        required: true
        schema:
          type: object
          properties:
            student_id: {type: string, example: "LD-2024-001"}
            name: {type: string, example: "Arjun"}
            q1_ambition: {type: string, example: "Cardiologist"}
    responses:
      200:
        description: Report generated successfully.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Empty or invalid JSON"}), 400

        student_id = data.get("student_id", "UNKNOWN")
        log.info(f"Evaluating student: {student_id}")

        result = generate_report(data)

        return jsonify({
            "status": "success",
            "student_id": student_id,
            "report": result["report"]
        })

    except Exception as e:
        log.error(f"Evaluation error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    log.info("Starting API on port 5005...")
    app.run(debug=False, host="0.0.0.0", port=5005)