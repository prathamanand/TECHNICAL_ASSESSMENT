import React, { useState } from "react";
import axios from "axios";

const backendUrl = "http://localhost:8000";

const ContractForm = () => {
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("explain");
  const [result, setResult] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResult("⏳ Loading...");
    try {
      const endpoint = mode === "explain" ? "/explain" : "/generate";
      const payload =
        mode === "explain" ? { input_text: input } : { specification: input };
      const res = await axios.post(`${backendUrl}${endpoint}`, payload);
      setResult(res.data.output);
    } catch (err) {
      setResult("❌ Error: " + err.response?.data?.detail || err.message);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <textarea
          rows={10}
          cols={80}
          placeholder={
            mode === "explain"
              ? "Enter contract address, file path, or raw code..."
              : "Describe what the contract should do..."
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <br />
        <label>
          <input
            type="radio"
            value="explain"
            checked={mode === "explain"}
            onChange={() => setMode("explain")}
          />
          Explain Contract
        </label>
        <label style={{ marginLeft: "1rem" }}>
          <input
            type="radio"
            value="generate"
            checked={mode === "generate"}
            onChange={() => setMode("generate")}
          />
          Generate Contract
        </label>
        <br />
        <button type="submit">Submit</button>
      </form>
      <pre style={{ marginTop: "1rem", backgroundColor: "#f4f4f4", padding: "1rem" }}>
        {result}
      </pre>
    </div>
  );
};

export default ContractForm;
