# SkillCast AI API — Complete Run Guide
**Leaders Desk Private Limited | Coimbatore**

---

## FIRST TIME SETUP (Run these only once)

### Step 1 — Create Virtual Environment
```bash
python3 -m venv venv
```

### Step 2 — Activate Virtual Environment
```bash
source venv/bin/activate
```
> You will see `(venv)` appear at the start of your terminal line.

### Step 3 — Install All Dependencies
```bash
pip install -r requirements.txt
```
> This installs Flask, Vertex AI SDK, flask-cors, and all other packages.

### Step 4 — Set Up Google Cloud Authentication
```bash
gcloud auth application-default login
```
> This opens a browser. Sign in with your Google account that has Vertex AI access.

### Step 5 — Set Your Google Cloud Project
```bash
gcloud config set project project-2d2fcb24-fa35-42f0-81f
```

### Step 6 — Verify Authentication Works
```bash
gcloud auth application-default print-access-token
```
> If you see a long token starting with `ya29.` — authentication is working. ✅

---

## DAILY RUN (Do this every time you want to start the API)

### Step 1 — Navigate to the project folder
```bash
cd /Users/akshay/Documents/skillcast_production
```

### Step 2 — Activate virtual environment
```bash
source venv/bin/activate
```

### Step 3 — Start the API server
```bash
python app.py
```

> The API will start and show:
> ```
> INFO  Connecting to Vertex AI...
> INFO  Vertex AI connected. Gemini 2.5 Flash loaded.
> INFO  Running on http://127.0.0.1:5005
> ```

---

## USING THE API

### Option A — Visual Tester (Recommended)
Open your browser and go to:
```
http://localhost:5005/tester
```
Paste student JSON data and click **Send Request**.

### Option B — Health Check (Quick test)
```
http://localhost:5005/health
```
Should return: `{ "status": "running", "model": "gemini-2.5-flash" }`

### Option C — Direct API Call (Terminal)
```bash
curl -X POST http://localhost:5005/evaluate \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Student", "school": "Test School", "group": "CS Group"}'
```

### Option D — Run the Test Script
```bash
python test_api.py
```

---


## IF AUTHENTICATION EXPIRES (Error: 401 Unauthorized)

Re-authenticate with Google:
```bash
gcloud auth application-default login
```



---

## API ENDPOINTS SUMMARY

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Auto-redirects to tester |
| GET | `/health` | Check if API is running |
| POST | `/evaluate` | Submit student data, get report |
| GET | `/tester` | Visual browser-based API tester |


