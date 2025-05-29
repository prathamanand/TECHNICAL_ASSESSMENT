import React, { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");
  const [mode, setMode] = useState("explain");

  const handleSubmit = async () => {
    const endpoint = mode === "explain" ? "/explain" : "/generate";
    const payload = mode === "explain" ? { input } : { spec: input };
    const res = await axios.post(`http://localhost:8000${endpoint}`, payload);
    setResponse(JSON.stringify(res.data, null, 2));
  };

  return (
    <div style={{ padding: 30 }}>
      <h2>Smart Contract Assistant</h2>
      <select onChange={e => setMode(e.target.value)} value={mode}>
        <option value="explain">Explain Contract</option>
        <option value="generate">Generate Solidity</option>
      </select>
      <textarea rows={10} cols={80} value={input} onChange={e => setInput(e.target.value)} />
      <br />
      <button onClick={handleSubmit}>Submit</button>
      <pre>{response}</pre>
    </div>
  );
}
