"""
FastAPI backend for the Diabetic Retinopathy Screening Chatbot module.

Endpoints:
    POST /chat                -> converse with the patient
    GET  /session/{session_id} -> fetch stored session JSON
    GET  /health               -> simple health check

This module ONLY implements the conversational intake chatbot. It does
NOT implement DR detection, image analysis, SHAP, PDF export, dashboards,
triage engines, or authentication.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core import session_manager, validation
from models.schemas import ChatRequest, ChatResponse, REQUIRED_FIELDS
from services.gemini_service import extract_information, GeminiServiceError

app = FastAPI(
    title="DR Screening Chatbot API",
    description="Conversational intake module for a diabetic retinopathy screening system.",
    version="1.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


FIELD_QUESTIONS = {
    "age": "Could you tell me your age?",
    "diabetes_duration": "How many years have you had diabetes?",
    "hba1c": "Do you know your most recent HbA1c value?",
    "blood_pressure": "Could you share your latest blood pressure reading (e.g. 120/80)?",
}

GREETING = (
    "Hi, I'm here to gather a few details about your health before your "
    "diabetic retinopathy screening. Could you start by telling me your "
    "age and how long you've had diabetes?"
)

COMPLETION_MESSAGE = (
    "Thank you. The required information has been collected successfully."
)


def _fallback_question(missing_fields: list) -> str:
    for field in REQUIRED_FIELDS:
        if field in missing_fields:
            return FIELD_QUESTIONS.get(field, f"Could you tell me your {field.replace('_', ' ')}?")
    return "Thank you, is there anything else about your eyes or health you'd like to add?"


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/session/{session_id}")
def get_session(session_id: str) -> Dict[str, Any]:
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required.")
    session = session_manager.load_session(session_id)
    return session


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    session_id = (payload.session_id or "").strip()
    message = (payload.message or "").strip()

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")

    session = session_manager.load_session(session_id)

    # Empty message handling: brand-new session gets a greeting instead
    # of an error; an empty message on an existing session is rejected.
    if not message:
        if not session["conversation_history"]:
            session_manager.append_turn(session, "assistant", GREETING)
            session_manager.save_session(session)
            return ChatResponse(
                reply=GREETING,
                patient_state=session,
                completed=session["completed"],
            )
        raise HTTPException(status_code=400, detail="message cannot be empty.")

    session_manager.append_turn(session, "user", message)

    # If we previously asked the patient to confirm a suspicious value,
    # handle that confirmation before running extraction again.
    if session.get("pending_confirmation"):
        pending = session["pending_confirmation"]
        lowered = message.lower()
        if any(word in lowered for word in ["yes", "correct", "right", "confirm"]):
            session["structured_data"][pending["field"]] = pending["value"]
        session["pending_confirmation"] = None

    try:
        extraction = extract_information(
            latest_message=message,
            conversation_history=session["conversation_history"],
            known_structured=session["structured_data"],
            known_dynamic=session["dynamic_data"],
        )
    except GeminiServiceError as exc:
        # Surface a clean error to the user instead of a stack trace,
        # and still persist the user's message so nothing is lost.
        # NOTE: we save here WITHOUT merging new data because we don't
        # have a successful extraction result — the session already has
        # whatever was previously saved, so no data is lost.
        session_manager.save_session(session)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    new_structured = extraction["structured_data"]
    new_dynamic = extraction["dynamic_data"]

    # Validate before merging: flag suspicious values for confirmation
    # rather than silently accepting impossible clinical numbers.
    suspicious_fields = validation.validate_structured_data(new_structured)

    if suspicious_fields:
        field = suspicious_fields[0]
        value = new_structured.pop(field)
        session_manager.merge_structured_data(session, new_structured)
        session_manager.merge_dynamic_data(session, new_dynamic)
        session["pending_confirmation"] = {"field": field, "value": value}
        reply = (
            f"Just to confirm — you mentioned {field.replace('_', ' ')} of "
            f"'{value}'. That looks unusual, could you double-check and "
            f"confirm it's correct?"
        )
        session_manager.append_turn(session, "assistant", reply)
        session_manager.save_session(session)
        return ChatResponse(reply=reply, patient_state=session, completed=False)

    session_manager.merge_structured_data(session, new_structured)
    session_manager.merge_dynamic_data(session, new_dynamic)

    missing = session_manager.get_missing_required_fields(session)
    completed = len(missing) == 0

    if completed:
        session["completed"] = True
        reply = COMPLETION_MESSAGE
    else:
        gemini_question = extraction.get("next_question") or ""
        # Safety check: if Gemini asks about a field that is already collected,
        # ignore its suggestion and use the deterministic fallback instead.
        already_collected = [
            f for f in REQUIRED_FIELDS
            if f not in missing
        ]
        question_mentions_collected = any(
            f.replace("_", " ") in gemini_question.lower() or f in gemini_question.lower()
            for f in already_collected
        )
        if gemini_question and not question_mentions_collected:
            reply = gemini_question
        else:
            reply = _fallback_question(missing)

    session_manager.append_turn(session, "assistant", reply)
    session_manager.save_session(session)

    return ChatResponse(reply=reply, patient_state=session, completed=completed)