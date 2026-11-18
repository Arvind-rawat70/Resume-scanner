import { useRef, useState } from "react";
import sampleJD from "../sampleJD.txt?raw";

export default function JDInput({ onExtract, loading, error }) {
  const [mode, setMode] = useState("paste");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const fileInput = useRef(null);

  const ready = mode === "paste" ? text.trim().length > 0 : !!file;

  function pickFile(f) {
    if (f) setFile(f);
  }

  return (
    <section className="panel" aria-labelledby="jd-heading">
      <h2 id="jd-heading">Job description</h2>

      <div className="tabs" role="tablist">
        {[["paste", "Paste text"], ["upload", "Upload file"]].map(([id, label]) => (
          <button key={id} role="tab" aria-selected={mode === id}
                  className={mode === id ? "tab active" : "tab"} onClick={() => setMode(id)}>
            {label}
          </button>
        ))}
      </div>

      {mode === "paste" ? (
        <>
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={18}
                    placeholder="Paste the full job description here, including requirements and responsibilities."
                    aria-label="Job description text" />
          <button className="link" onClick={() => setText(sampleJD)}>Use a sample job description</button>
        </>
      ) : (
        <div className={dragging ? "drop dragging" : "drop"}
             onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
             onDragLeave={() => setDragging(false)}
             onDrop={(e) => { e.preventDefault(); setDragging(false); pickFile(e.dataTransfer.files[0]); }}>
          <input ref={fileInput} type="file" hidden accept=".pdf,.docx,.txt"
                 onChange={(e) => pickFile(e.target.files[0])} />
          {file ? (
            <p><strong>{file.name}</strong><br /><span className="muted">{(file.size / 1024).toFixed(0)} KB</span></p>
          ) : (
            <p>Drop a PDF, DOCX or TXT file here</p>
          )}
          <button className="secondary" onClick={() => fileInput.current.click()}>
            {file ? "Choose a different file" : "Choose file"}
          </button>
        </div>
      )}

      {error && <p className="error" role="alert">{error}</p>}

      <button className="primary" disabled={!ready || loading}
              onClick={() => onExtract(mode === "paste" ? { text } : { file })}>
        {loading ? "Extracting…" : "Extract requirements"}
      </button>
    </section>
  );
}
