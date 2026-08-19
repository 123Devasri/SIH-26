# DR Screening Chatbot Module

A conversational intake chatbot for an AI-based Diabetic Retinopathy
screening system. This module **only** handles the patient conversation:
collecting clinical information in natural language, extracting it with
Grok, tracking conversation state, and exporting patient JSON for a
downstream screening pipeline.

It does **not** include DR detection, fundus image analysis, SHAP,
PDF generation, dashboards, triage engines, or authentication — those
are separate modules.

---

## 1. Folder Structure

```
dr-chatbot/
├── backend/
│   ├── main.py                    # FastAPI app, /chat and /session endpoints
│   ├── requirements.txt
│   ├── .env.example
│   ├── data/                      # session_<id>.json files are written here
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic models + core field list
│   ├── services/
│   │   ├── __init__.py
│   │   └── grok_service.py        # Grok (xAI) extraction engine
│   └── core/
│       ├── __init__.py
│       ├── session_manager.py     # JSON-file session storage & merging
│       └── validation.py          # Clinical value range validation
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    ├── .env.example
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── App.css
        ├── api/
        │   └── chatApi.js
        └── components/
            ├── ChatWindow.jsx
            ├── MessageBubble.jsx
            ├── TypingIndicator.jsx
            └── InputBox.jsx
```

---

## 2. Installation Steps

Prerequisites: **Python 3.11+**, **Node.js 18+**, and a Grok (xAI) API key
from https://console.x.ai.

### Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set your key:

```
GROK_API_KEY=your_actual_key_here
GROK_MODEL=grok-2-latest
GROK_BASE_URL=https://api.x.ai/v1
DATA_DIR=data
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Run the backend:

```bash
uvicorn main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`. Interactive docs at
`http://localhost:8000/docs`.

### Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
```

Edit `frontend/.env` if your backend runs somewhere other than
`http://localhost:8000`:

```
VITE_API_BASE_URL=http://localhost:8000
```

Run the frontend:

```bash
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 3. Environment Variables

| File               | Variable            | Description                                   |
|--------------------|----------------------|------------------------------------------------|
| backend/.env       | `GROK_API_KEY`       | Your xAI Grok API key (required)               |
| backend/.env       | `GROK_MODEL`         | Grok model name (default `grok-2-latest`)       |
| backend/.env       | `GROK_BASE_URL`      | xAI OpenAI-compatible base URL                  |
| backend/.env       | `DATA_DIR`           | Folder for session JSON files (default `data`)  |
| backend/.env       | `ALLOWED_ORIGINS`    | Comma-separated CORS origins                    |
| frontend/.env      | `VITE_API_BASE_URL`  | URL of the FastAPI backend                      |

---

## 4. Run Commands (quick reference)

```bash
# Terminal 1 — backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

---

## 5. API Reference

### `POST /chat`

Request:
```json
{ "session_id": "abc123", "message": "I am 56 years old and diabetic for 12 years." }
```

Response:
```json
{
  "reply": "Thanks. Do you know your most recent HbA1c value?",
  "patient_state": {
    "session_id": "abc123",
    "structured_data": { "age": 56, "diabetes_duration": 12, "...": null },
    "dynamic_data": {},
    "conversation_history": [ { "role": "user", "message": "...", "timestamp": "..." } ],
    "completed": false
  },
  "completed": false
}
```

### `GET /session/{session_id}`

Returns the full stored session JSON (same shape as `patient_state` above).

---

## 6. Testing Instructions

### Manual test via curl

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test1","message":"I am 56 years old and diabetic for 12 years."}'

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test1","message":"My HbA1c was around 9.2 last month, and my blood pressure was 130/85."}'

curl http://localhost:8000/session/test1
```

The second call above should include all four required fields
(`age`, `diabetes_duration`, `hba1c`, `blood_pressure`) and the response
should return `"completed": true`.

### Manual test via UI

1. Start backend and frontend as described above.
2. Open the app; the assistant greets you automatically.
3. Type natural sentences, e.g.:
   - "I am 56 years old and diabetic for 12 years."
   - "My HbA1c was around 9.2 last month."
   - "My vision gets blurry at night, and my father also had diabetic retinopathy."
   - "My blood pressure yesterday was 130/85."
4. Confirm the chat becomes complete once the four required fields are known.
5. Refresh the page — the conversation should reload from the stored session
   (via `localStorage` session id + `GET /session/{id}`).
6. Click **New Session** to start over with a fresh `session_id`.

### Error-handling checks

- Stop the backend and send a message → frontend shows a network error banner.
- Remove `GROK_API_KEY` from `.env` and restart backend → `/chat` returns
  a 502 with a clear "GROK_API_KEY is not set" message.
- Manually corrupt a `backend/data/session_<id>.json` file (e.g. truncate it)
  → next request for that session starts fresh instead of crashing, and the
  corrupted file is backed up alongside it.
- Send `{"session_id": "", "message": "hi"}` → 400 error, "session_id is required."

---

## 7. Data Model Notes

Each session is stored as `backend/data/session_<session_id>.json`:

```json
{
  "session_id": "abc123",
  "structured_data": { "age": 56, "hba1c": 9.2, "...": null },
  "dynamic_data": { "family_history": "Father had diabetic retinopathy" },
  "conversation_history": [ { "role": "user", "message": "...", "timestamp": "..." } ],
  "completed": true,
  "pending_confirmation": null
}
```

This file is the export format consumed by the downstream DR screening
AI pipeline — no database is used, and no information outside the core
fields is ever discarded (it lands in `dynamic_data`).
