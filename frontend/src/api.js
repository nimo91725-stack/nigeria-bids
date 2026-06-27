import axios from "axios";

const api = axios.create({ baseURL: "/api" });

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
