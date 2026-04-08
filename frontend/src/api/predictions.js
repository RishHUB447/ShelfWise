import axios from "axios";

const BASE_URL = "http://localhost:8000";

export const predictDemand = async (data) => {
  const response = await axios.post(`${BASE_URL}/predictions/predict`, data);
  return response.data;
};

export const getPredictionHistory = async (productId) => {
  const response = await axios.get(`${BASE_URL}/predictions/history/${productId}`);
  return response.data;
};