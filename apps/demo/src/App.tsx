import { useRef, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:3000';

interface OcrResponse {
  text: string;
  recordId: string;
}

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OcrResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
    setResult(null);
    setError(null);
    if (selected) {
      setPreview(URL.createObjectURL(selected));
    } else {
      setPreview(null);
    }
  }

  async function handleRunOcr() {
    if (!file) {
      setError('Please select an image first.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image', file);

      const res = await fetch(`${API_BASE}/records/ocr`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const body = await res.text();
        throw new Error(`API error ${res.status}: ${body}`);
      }

      const data: OcrResponse = await res.json();
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <h1>AI Habit Platform</h1>
      <p className="subtitle">OCR Demo — upload a nutrition label or any text image</p>

      <div className="card">
        <div className="upload-area" onClick={() => inputRef.current?.click()}>
          {preview ? (
            <img src={preview} alt="preview" className="preview-img" />
          ) : (
            <div className="upload-placeholder">
              <span className="upload-icon">+</span>
              <span>Click to select an image</span>
            </div>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
        </div>

        {file && (
          <p className="file-name">{file.name}</p>
        )}

        <button
          className="btn-primary"
          onClick={handleRunOcr}
          disabled={loading || !file}
        >
          {loading ? 'Processing...' : 'Run OCR'}
        </button>
      </div>

      {error && (
        <div className="result-card error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="result-card success">
          <div className="result-header">
            <span className="badge">OCR Result</span>
            <span className="record-id">Record ID: {result.recordId}</span>
          </div>
          <pre className="result-text">{result.text || '(no text extracted)'}</pre>
        </div>
      )}
    </div>
  );
}
