import { useRef, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:3000';

interface OcrResponse {
  text: string;
  recordId: string;
  productName: string | null;
  calories: number | null;
  protein: string | null;
}

interface CalendarEventResponse {
  eventId: string;
  htmlLink: string;
}

interface NotificationResponse {
  messageId: string;
  token: string;
}

export default function App() {
  // OCR
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrResult, setOcrResult] = useState<OcrResponse | null>(null);
  const [ocrError, setOcrError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Calendar
  const [calType, setCalType] = useState<'meal' | 'water'>('meal');
  const [calTime, setCalTime] = useState('');
  const [calLoading, setCalLoading] = useState(false);
  const [calResult, setCalResult] = useState<CalendarEventResponse | null>(null);
  const [calError, setCalError] = useState<string | null>(null);

  // Notification
  const [notiMessage, setNotiMessage] = useState("Don't forget to log your meal!");
  const [notiLoading, setNotiLoading] = useState(false);
  const [notiResult, setNotiResult] = useState<NotificationResponse | null>(null);
  const [notiError, setNotiError] = useState<string | null>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
    setOcrResult(null);
    setOcrError(null);
    if (selected) {
      setPreview(URL.createObjectURL(selected));
    } else {
      setPreview(null);
    }
  }

  async function handleRunOcr() {
    if (!file) {
      setOcrError('Please select an image first.');
      return;
    }
    setOcrLoading(true);
    setOcrError(null);
    setOcrResult(null);
    try {
      const formData = new FormData();
      formData.append('image', file);
      const res = await fetch(`${API_BASE}/records/ocr`, { method: 'POST', body: formData });
      if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
      setOcrResult(await res.json());
    } catch (err: unknown) {
      setOcrError(err instanceof Error ? err.message : String(err));
    } finally {
      setOcrLoading(false);
    }
  }

  async function handleCreateEvent() {
    if (!calTime) {
      setCalError('날짜/시간을 선택해주세요.');
      return;
    }
    setCalLoading(true);
    setCalError(null);
    setCalResult(null);
    try {
      const res = await fetch(`${API_BASE}/calendar/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: calType, time: calTime }),
      });
      if (!res.ok) {
        const body = await res.json();
        throw new Error(body.message ?? `API error ${res.status}`);
      }
      setCalResult(await res.json());
    } catch (err: unknown) {
      setCalError(err instanceof Error ? err.message : String(err));
    } finally {
      setCalLoading(false);
    }
  }

  async function handleSendNotification() {
    if (!notiMessage.trim()) {
      setNotiError('메시지를 입력해주세요.');
      return;
    }
    setNotiLoading(true);
    setNotiError(null);
    setNotiResult(null);
    try {
      const res = await fetch(`${API_BASE}/notifications/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: notiMessage }),
      });
      if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
      setNotiResult(await res.json());
    } catch (err: unknown) {
      setNotiError(err instanceof Error ? err.message : String(err));
    } finally {
      setNotiLoading(false);
    }
  }

  return (
    <div className="container">
      <h1>AI Habit Platform</h1>
      <p className="subtitle">OCR + LLM + Google Calendar + FCM Demo</p>

      {/* Phase 2/3 — OCR */}
      <section>
        <h2 className="section-title">Phase 2/3 — OCR + LLM 구조화</h2>
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
          {file && <p className="file-name">{file.name}</p>}
          <button className="btn-primary" onClick={handleRunOcr} disabled={ocrLoading || !file}>
            {ocrLoading ? 'Processing...' : 'Run OCR'}
          </button>
        </div>
        {ocrError && <div className="result-card error"><strong>Error:</strong> {ocrError}</div>}
        {ocrResult && (
          <div className="result-card success">
            <div className="result-header">
              <span className="badge">OCR Result</span>
              <span className="record-id">Record ID: {ocrResult.recordId}</span>
            </div>
            <pre className="result-text">{ocrResult.text || '(no text extracted)'}</pre>
            {ocrResult.productName && (
              <div className="llm-result">
                <div><strong>상품명:</strong> {ocrResult.productName}</div>
                <div><strong>칼로리:</strong> {ocrResult.calories} kcal</div>
                <div><strong>단백질:</strong> {ocrResult.protein}</div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Phase 4 — Google Calendar */}
      <section>
        <h2 className="section-title">Phase 4 — Google Calendar 리마인더</h2>
        <div className="card">
          <p className="section-desc">
            먼저 Google 계정으로 인증한 후 캘린더 이벤트를 생성하세요.
          </p>
          <button
            className="btn-secondary"
            onClick={() => window.open(`${API_BASE}/auth/google`, '_blank')}
          >
            Google Calendar 인증하기
          </button>
          <div className="form-row" style={{ marginTop: '16px' }}>
            <select
              value={calType}
              onChange={(e) => setCalType(e.target.value as 'meal' | 'water')}
              className="select-input"
            >
              <option value="meal">식사 리마인더</option>
              <option value="water">물 마시기 리마인더</option>
            </select>
            <input
              type="datetime-local"
              value={calTime}
              onChange={(e) => setCalTime(e.target.value)}
              className="datetime-input"
            />
          </div>
          <button className="btn-primary" onClick={handleCreateEvent} disabled={calLoading}>
            {calLoading ? '생성 중...' : '이벤트 추가'}
          </button>
        </div>
        {calError && <div className="result-card error"><strong>Error:</strong> {calError}</div>}
        {calResult && (
          <div className="result-card success">
            <div className="result-header">
              <span className="badge">Calendar Event</span>
            </div>
            <p>이벤트 ID: {calResult.eventId}</p>
            <a href={calResult.htmlLink} target="_blank" rel="noreferrer">
              Google Calendar에서 보기
            </a>
          </div>
        )}
      </section>

      {/* Phase 4 — FCM Push Notification */}
      <section>
        <h2 className="section-title">Phase 4 — FCM 푸시 알림</h2>
        <div className="card">
          <p className="section-desc">테스트 디바이스로 푸시 알림을 전송합니다.</p>
          <input
            type="text"
            value={notiMessage}
            onChange={(e) => setNotiMessage(e.target.value)}
            className="text-input"
            placeholder="알림 메시지 입력"
          />
          <button className="btn-primary" onClick={handleSendNotification} disabled={notiLoading}>
            {notiLoading ? '전송 중...' : '알림 보내기'}
          </button>
        </div>
        {notiError && <div className="result-card error"><strong>Error:</strong> {notiError}</div>}
        {notiResult && (
          <div className="result-card success">
            <div className="result-header">
              <span className="badge">FCM Sent</span>
            </div>
            <p>Message ID: {notiResult.messageId}</p>
          </div>
        )}
      </section>
    </div>
  );
}
