import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

/**
 * Send a chat message to the backend.
 * @param {string} sessionId
 * @param {string} message
 * @returns {Promise<{reply: string, patient_state: object, completed: boolean}>}
 */
export async function sendMessage(sessionId, message) {
  try {
    const response = await client.post("/chat", {
      session_id: sessionId,
      message,
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      const detail = error.response.data?.detail || "The server returned an error.";
      throw new Error(detail);
    }
    if (error.request) {
      throw new Error("Could not reach the server. Please check your connection.");
    }
    throw new Error(error.message || "Something went wrong.");
  }
}

/**
 * Fetch the stored session state (used to restore a persisted session).
 * @param {string} sessionId
 */
export async function fetchSession(sessionId) {
  try {
    const response = await client.get(`/session/${sessionId}`);
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data?.detail || "Could not load session.");
    }
    throw new Error("Could not reach the server. Please check your connection.");
  }
}
