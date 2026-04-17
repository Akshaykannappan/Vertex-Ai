# SkillCast AI Assessment API — Backend Integration Guide

This document outlines the technical requirements for integrating the backend systems with the SkillCast AI Assessment API. This API evaluates a student's psychometric profile and autonomously generates a comprehensive career report using Vertex AI.

---

## 1. Quick Links
- **Interactive Swagger Dashboard:** [https://skillcast-api-1051474812711.us-central1.run.app/apidocs/](https://skillcast-api-1051474812711.us-central1.run.app/apidocs/) 
  *(Use this dashboard to visually test endpoints and automatically view schema constraints)*

---

## 2. API Endpoint Details 

The core evaluation endpoint handles processing and report generation entirely autonomously. No authentication tokens or API keys are required for this internal service.

- **Base URL:** `https://skillcast-api-1051474812711.us-central1.run.app`
- **Path:** `/evaluate`
- **Method:** `POST`
- **Headers Required:** 
  - `Content-Type: application/json`

---

## 3. Request Payload (Input JSON)

The backend must POST the student's raw assessment data to the `/evaluate` endpoint. Please ensure the payload perfectly matches the structure below.

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

## 4. Response Payload (Output JSON)

Once processed, the API will return the generated AI Career Report in the following structured JSON format. A successful request returns a `200 OK` status with the `status: "success"` property.

```json
{
  "status": "success",
  "student_id": "STU001",
  "report": {
    "student_name": "Student Name",
    "school": "School Name",
    "group": "Bio-Maths",
    "year": "2025-26",
    "introduction": "This student is highly inclined towards biology...",
    "skills": {
      "reasoning": ["Observation 1", "Observation 2"],
      "numerical": ["Observation 1", "Observation 2"],
      "scientific": ["Observation 1", "Observation 2", "Observation 3"],
      "spatial":   ["Observation 1", "Observation 2"],
      "system":    ["Observation 1", "Observation 2"],
      "verbal":    ["Observation 1", "Observation 2"]
    },
    "personality": {
      "intro":         "Personality overview paragraph...",
      "realistic":     "Specific realistic trait breakdown...",
      "investigative": "Specific investigative trait breakdown...",
      "artistic":      "Specific artistic trait breakdown...",
      "social":        "Specific social trait breakdown...",
      "enterprising":  "Specific enterprising trait breakdown...",
      "conventional":  "Specific conventional trait breakdown..."
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
    "conclusion": "Final concluding remarks for the student..."
  }
}
```
