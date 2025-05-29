import axios from "axios";

export const generateSolidity = (prompt) =>
  axios.post("http://localhost:8000/generate", { prompt });
