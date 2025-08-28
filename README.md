# SKILL Gap MVP - 60-minute thin slice

This is a minimal, runnable MVP for the SKILL Gap Analysis Tool. It implements:
- /diagnostics/generate : accepts item responses and returns mastery_vector, gaps, curriculum_plan, predictions
- /health : healthcheck

## Run locally (recommended for the 60-minute demo)

1. Create & activate a Python venv
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Start the API
   ```bash
   uvicorn main:app --reload --port 8080
   ```

3. In another terminal run the sample payload:
   ```bash
   curl -s -X POST http://127.0.0.1:8080/diagnostics/generate \
     -H "Content-Type: application/json" \
     -d @sample_payload.json | jq .
   ```

## Docker (optional)
Build & run with docker-compose:
```
docker compose up --build -d
```

## What to submit for the internship
- The project ZIP or GitHub link
- `mvp_result.json` (API response saved)
- Short note: Baseline Beta-Binomial mastery; simple gap thresholds; curriculum plan baseline; naive prediction baseline.
