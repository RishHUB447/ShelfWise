import axios from "axios";

const BASE_URL = "http://localhost:8000";

const getHeaders = () => {
  const token = localStorage.getItem("shelfwise_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("shelfwise_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const register = (data) => api.post("/auth/register", data);
export const login = (data) => api.post("/auth/login", data);
export const predictDemand = (data) => api.post("/predictions/predict", data);
export const getPredictionHistory = (productId) => api.get(`/predictions/history/${productId}`);