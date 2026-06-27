import axios from "axios";

// In production (Vercel) use the GCP Cloud Run backend URL via env var.
// In local dev, Vite proxy rewrites /api → localhost:8000.
const BASE_URL = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({ baseURL: BASE_URL });

export const getOpportunities = (params) =>
  api.get("/opportunities/", { params }).then((r) => r.data);

export const getOpportunity = (id) =>
  api.get(`/opportunities/${id}`).then((r) => r.data);

export const createOpportunity = (data) =>
  api.post("/opportunities/", data).then((r) => r.data);

export const updateOpportunity = (id, data) =>
  api.patch(`/opportunities/${id}`, data).then((r) => r.data);

export const deleteOpportunity = (id) =>
  api.delete(`/opportunities/${id}`);

export const scrapeAll = () =>
  api.post("/scrape/all").then((r) => r.data);

export const scrapeSource = (source) =>
  api.post(`/scrape/${source}`).then((r) => r.data);

export const getAlerts = () =>
  api.get("/alerts/").then((r) => r.data);

export const createAlert = (data) =>
  api.post("/alerts/", data).then((r) => r.data);

export const deleteAlert = (id) =>
  api.delete(`/alerts/${id}`);
