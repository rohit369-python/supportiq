import axios from "axios";
import { useAuthStore } from "../store/auth";

const API_URL = import.meta.env.VITE_API_URL || "/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export async function login(email: string, password: string) {
  const { data } = await api.post("/auth/login", { email, password });
  return data;
}

export async function getMe() {
  const { data } = await api.get("/auth/me");
  return data;
}

export async function listTickets(params?: Record<string, any>) {
  const { data } = await api.get("/tickets", { params });
  return data;
}

export async function getTicket(id: string) {
  const { data } = await api.get(`/tickets/${id}`);
  return data;
}

export async function createTicket(payload: {
  customer_id: string;
  subject: string;
  description: string;
  priority?: string;
}) {
  const { data } = await api.post("/tickets", payload);
  return data;
}

export async function sendChatMessage(message: string, conversationId?: string) {
  const { data } = await api.post("/chatbot/message", {
    message,
    conversation_id: conversationId,
  });
  return data;
}