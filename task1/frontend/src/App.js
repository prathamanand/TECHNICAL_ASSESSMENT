import React, { useState } from "react";
import axios from "axios";
import "./App.css";

export default function App() {
  const [input, setInput] = useState("");
  const [code, setCode] = useState("");
  const [explanation, setExplanation] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!input.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post("http://localhost:8000/generate", { prompt: input });
      setCode(res.data.solidity_code || "");
      setExplanation(res.data.explanation || "");
    } catch (e) {
      alert("Something went wrong: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1>🧠 NL ➝ Solidity Generator</h1>
      <textarea
        placeholder="e.g., Create an ERC-20 token with minting restricted to an allowlist"
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />
      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "Generating..." : "Generate Solidity"}
      </button>

      {code && (
        <>
          <h2>✅ Solidity Code</h2>
          <pre className="code-block">{code}</pre>
          <h2>🛡️ Explanation</h2>
          <p className="explanation">{explanation}</p>
        </>
      )}
    </div>
  );
}
