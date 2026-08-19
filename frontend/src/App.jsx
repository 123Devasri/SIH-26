import React, { useEffect, useRef, useState, useCallback } from "react";
import ChatWindow from "./components/ChatWindow.jsx";
import InputBox from "./components/InputBox.jsx";
import { sendMessage, fetchSession } from "./api/chatApi.js";

const SESSION_STORAGE_KEY = "dr_chatbot_session_id";

function generateSessionId() {
  return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

export default function App() {
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [startupError, setStartupError] = useState("");
  const [error, setError] = useState("");
  const [completed, setCompleted] = useState(false);
  const initialized = useRef(false);
  const currentSessionIdRef = useRef("");

  const startSession = useCallback(async (existingId) => {
    setIsLoadingSession(false);
    setStartupError("");
    setError("");
    try {
      setIsTyping(true);
      const data = await sendMessage(existingId, "");
      setMessages(data.patient_state.conversation_history);
      setCompleted(data.completed);
    } catch (err) {
      setStartupError(err.message);
    } finally {
      setIsTyping(false);
    }
  }, []);

  const init = useCallback(async () => {
    let existingId = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!existingId) {
      existingId = generateSessionId();
      localStorage.setItem(SESSION_STORAGE_KEY, existingId);
    }
    currentSessionIdRef.current = existingId;
    setSessionId(existingId);

    try {
      const session = await fetchSession(existingId);
      if (session.conversation_history && session.conversation_history.length > 0) {
        setMessages(session.conversation_history);
        setCompleted(!!session.completed);
        setIsLoadingSession(false);
        return;
      }
    } catch (_) {
      // No existing session yet — that's fine, we'll start a new one.
    }

    await startSession(existingId);
  }, [startSession]);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    init();
  }, [init]);

  const handleSend = async (text) => {
    setError("");
    setStartupError("");
    const sid = currentSessionIdRef.current || sessionId;
    const optimisticMsg = { role: "user", message: text };
    setMessages((prev) => [...prev, optimisticMsg]);
    setIsTyping(true);
    try {
      const data = await sendMessage(sid, text);
      setMessages(data.patient_state.conversation_history);
      setCompleted(data.completed);
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m !== optimisticMsg));
      setError(err.message);
    } finally {
      setIsTyping(false);
    }
  };

  const handleNewSession = () => {
    const newId = generateSessionId();
    localStorage.setItem(SESSION_STORAGE_KEY, newId);
    setSessionId(newId);
    currentSessionIdRef.current = newId;
    setMessages([]);
    setCompleted(false);
    setError("");
    setStartupError("");
    initialized.current = false;
    window.location.reload();
  };

  const combinedError = error || startupError;

  return (
    <div className="app-container">
      <header className="app-header">
        <div>
          <h1>DR Screening Assistant</h1>
          <p className="app-subtitle">Pre-screening intake conversation</p>
        </div>
        <button className="new-session-button" onClick={handleNewSession}>
          New Session
        </button>
      </header>

      {completed && (
        <div className="completion-banner">
          Intake complete — your information has been recorded for the
          screening pipeline.
        </div>
      )}

      {isLoadingSession ? (
        <div className="loading-container">Loading conversation...</div>
      ) : (
        <ChatWindow messages={messages} isTyping={isTyping} error={combinedError} />
      )}

      {startupError && !isLoadingSession && messages.length === 0 && (
        <div style={{ textAlign: "center", padding: "0 1rem 0.5rem" }}>
          <button
            className="new-session-button"
            onClick={() => {
              initialized.current = false;
              startSession(currentSessionIdRef.current || sessionId);
            }}
          >
            Retry Connection
          </button>
        </div>
      )}

      <InputBox onSend={handleSend} disabled={isTyping || isLoadingSession} />
    </div>
  );
}
