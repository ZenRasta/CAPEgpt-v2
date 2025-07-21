import { useState } from 'react';
import MathJax from 'mathjax-react';

function App() {
  const [image, setImage] = useState(null);
  const [subject, setSubject] = useState('Pure Mathematics');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    setLoading(true);
    const formData = new FormData();
    formData.append('file', image);
    const ocrRes = await fetch('http://127.0.0.1:8000/upload', { method: 'POST', body: formData });
    const { text } = await ocrRes.json();
    const queryRes = await fetch('http://127.0.0.1:8000/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, subject })
    });
    const data = await queryRes.json();
    setResponse(data);
    setLoading(false);
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl">CAPE GPT</h1>
      <select value={subject} onChange={(e) => setSubject(e.target.value)} className="border p-2">
        <option>Pure Mathematics</option>
        {/* Add more subjects */}
      </select>
      <input type="file" onChange={(e) => setImage(e.target.files[0])} className="block my-2" />
      <button onClick={handleUpload} disabled={!image || loading} className="bg-blue-500 text-white p-2">Submit</button>
      {loading && <p>Loading...</p>}
      {response && (
        <div>
          <h2>Solution:</h2>
          <MathJax.Provider><MathJax.Node formula={response.answer} /></MathJax.Provider>
          <h3>Years appeared:</h3>
          <p>{response.years.join(', ')}</p>
          <h3>Topics:</h3>
          <p>{response.topics.join(', ')}</p>
        </div>
      )}
    </div>
  );
}

export default App;
