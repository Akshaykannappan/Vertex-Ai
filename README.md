# Leaders Desk SkillCast AI — Step by Step Setup Guide

## What This System Does

A student completes the psychometric assessment.
Their answers are sent to this API.
Vertex AI RAG retrieves relevant career guidance from the knowledge base.
Gemini 2.5 Flash analyses the answers and generates the complete Skill Cast Report.
The report is returned as JSON to the software team.

---

## Files in This Folder

| File | Purpose |
|---|---|
| `app.py` | Complete API — contains everything in one file |
| `setup_corpus.py` | Run once to create the Vertex AI knowledge base |
| `test_api.py` | Test the running API |
| `answer_mapping.txt` | 36 counsellor-evaluated student profiles (upload to bucket) |
| `requirements.txt` | Python packages to install |
| `Dockerfile` | For Cloud Run deployment |
| `.env.example` | Copy to `.env` and fill in your values |

---

## STEP 1 — Install Python Packages

Open Terminal and run:

```bash
pip install flask google-cloud-aiplatform python-dotenv gunicorn
```

---

## STEP 2 — Google Cloud Setup (One Time)

### 2a — Enable APIs

Go to console.cloud.google.com

Enable these two APIs:
- Vertex AI API
- Cloud Storage API

### 2b — Create Storage Bucket

Go to Cloud Storage → Buckets → Create

```
Bucket name:  skillcast-career-data
Region:       us-central1
Storage class: Standard
```

### 2c — Upload Files to Bucket

Upload these files to the bucket:
- `answer_mapping.txt` (from this folder — 36 student profiles)
- `careers_jobs.txt` (job database — convert to .txt)
- `tnea_cutoff.txt` (TNEA cutoff data — convert to .txt)
- `report_template.txt` (Skill Cast Report format — convert to .txt)

### 2d — Add Developer Access

Go to IAM & Admin → IAM → Grant Access

Add these as Owner:
- mcagokul4@gmail.com
- sarankumar2622@gmail.com

---

## STEP 3 — Create the Knowledge Base (One Time)

Open `setup_corpus.py` and replace `YOUR_PROJECT_ID` on line 22 with your actual project ID.

Run:
```bash
python setup_corpus.py
```

Wait 5-7 minutes. At the end it will print your CORPUS NAME like:
```
projects/123456789/locations/us-central1/ragCorpora/987654321
```

Copy this entire line.

---

## STEP 4 — Create Your .env File

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and fill in:
```
GOOGLE_CLOUD_PROJECT=your-actual-project-id
VERTEX_CORPUS_NAME=projects/xxx/locations/us-central1/ragCorpora/xxx
LOCATION=us-central1
```

---

## STEP 5 — Run Locally and Test

Start the API:
```bash
python app.py
```

In a new terminal, run the test:
```bash
python test_api.py
```

If you see `ALL TESTS PASSED` — you are ready to deploy.

---

## STEP 6 — Deploy to Google Cloud Run

```bash
gcloud run deploy skillcast-ai \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id \
  --set-env-vars VERTEX_CORPUS_NAME=your-corpus-name \
  --set-env-vars LOCATION=us-central1
```

Wait 3-5 minutes. You will receive a URL like:
```
https://skillcast-ai-abc123-uc.a.run.app
```

Test the deployed API:
```bash
python test_api.py https://skillcast-ai-abc123-uc.a.run.app
```

---

## STEP 7 — Share URL With Software Team

Give the software team:

```
Base URL:  https://skillcast-ai-abc123-uc.a.run.app
Endpoint:  POST /evaluate
Health:    GET  /health
```

---

## API Input Format

Send POST to `/evaluate` with this JSON:

```json
{
  "student_id": "STU001",
  "name": "Student Name",
  "school": "School Name",
  "group": "Bio-Maths",
  "year": "2025-26",
  "ambition_yn": "Yes",
  "ambition_specify": "Doctor",
  "can_achieve": "Yes",
  "strength": "Hard working",
  "weakness": "Time management",
  "subject_score": "70",
  "subject_level": "Good",
  "subjects_liked": ["Biology", "Chemistry"],
  "subjects_disliked": ["Physics"],
  "interests": ["NCC"],
  "passion": "Medicine",
  "learn": ["Public Speaking"],
  "char_a": "Helpful",
  "char_b": "Hardworking",
  "char_c": "Creative",
  "proud_of": "Winning science competition",
  "inspires": "APJ Abdul Kalam",
  "organise": "Yes",
  "stage_feeling": ["Nervous"],
  "physical": ["No"],
  "study_time": "Night",
  "alone": "Sometimes",
  "repair": "No",
  "considers_others": "Always",
  "adjusts": "Often",
  "insensitive": "Never",
  "abilities": ["teaching, counselling, nursing, or giving information"],
  "opinions": ["helpful, friendly, trustworthy"],
  "values": ["values helping people and practical knowledge"],
  "occ_analytical": [],
  "occ_pragmatic": [],
  "occ_social": ["Nurse", "Teacher"],
  "occ_creative": [],
  "occ_enterprising": [],
  "occ_conventional": ["Doctor"],
  "life_skills": {
    "q1_confident":   "Often",
    "q2_introduce":   "Sometimes",
    "q3_listener":    "Always",
    "q4_ask_help":    "Often",
    "q5_suggestions": "Always",
    "q6_trust":       "Often",
    "q7_concentrate": "Never",
    "q8_decisions":   "Sometimes",
    "q9_positive":    "Rarely",
    "q10_say_no":     "Sometimes"
  },
  "cognitive": {
    "subjects_preferred": "Maths/Science",
    "punctuality":        "Well before time",
    "movie_focus":        "Story Line",
    "maths_comfort":      "Number calculations",
    "project_approach":   "Organise and complete one by one",
    "memory_type":        "Face",
    "problem_solving":    "Analyse logically",
    "pear_answer":        "40 cents"
  }
}
```

---

## API Output Format

```json
{
  "status": "success",
  "student_id": "STU001",
  "report": {
    "student_name": "Student Name",
    "school": "School Name",
    "group": "Bio-Maths",
    "year": "2025-26",
    "introduction": "paragraph...",
    "skills": {
      "reasoning": ["bullet 1", "bullet 2"],
      "numerical": ["bullet 1", "bullet 2"],
      "scientific": ["bullet 1", "bullet 2", "bullet 3"],
      "spatial":   ["bullet 1", "bullet 2"],
      "system":    ["bullet 1", "bullet 2"],
      "verbal":    ["bullet 1", "bullet 2"]
    },
    "personality": {
      "intro":         "paragraph...",
      "realistic":     "paragraph...",
      "investigative": "paragraph...",
      "artistic":      "paragraph...",
      "social":        "paragraph...",
      "enterprising":  "paragraph...",
      "conventional":  "paragraph..."
    },
    "overall_analysis": {
      "high_interest":     ["Research", "Creative", "Managerial"],
      "moderate_interest": ["Administrative"],
      "low_interest":      ["Computational"]
    },
    "recommendations": [
      "BSc Nursing — suited given Biology preference and social interest",
      "Optometry — recommended for Allied Health Sciences path",
      "BTech Biomedical Engineering — suits Bio-Maths combination"
    ],
    "conclusion": "paragraph..."
  }
}
```

---

## Updating the Knowledge Base

When new data arrives (updated cutoffs, new jobs, new student profiles):

1. Convert the new file to .txt
2. Upload to Cloud Storage bucket
3. Re-run `python setup_corpus.py`

No code change needed. Takes less than 10 minutes.

---

## Common Errors and Fixes

| Error | Fix |
|---|---|
| `GOOGLE_CLOUD_PROJECT not set` | Check your .env file has the correct project ID |
| `VERTEX_CORPUS_NAME not set` | Run setup_corpus.py and copy the corpus name to .env |
| `No JSON object found` | Try the request again — Gemini occasionally returns unexpected format |
| `Connection refused on port 5001` | Start the API first: `python app.py` |
| `Permission denied` | Make sure your Google account is added as Owner in IAM |
