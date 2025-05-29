import { useState } from 'react';
import axios from 'axios';

function App() {
  const [input, setInput] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!input) return;

    setLoading(true);
    setResponse('');

    try {
      const res = await axios.post('http://localhost:8000/explain', { input });
      setResponse(res.data.output);
    } catch (error) {
      setResponse("Error: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 40 }}>
      <h1>Solidity Contract Explainer</h1>
      <textarea
        rows="5"
        cols="70"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Enter contract address or Solidity code"
      />
      <br /><br />
      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "Analyzing..." : "Submit"}
      </button>
      <br /><br />
      <pre style={{ whiteSpace: 'pre-wrap', background: '#f0f0f0', padding: 20 }}>
        {response}
      </pre>
    </div>
  );
}

export default App;
