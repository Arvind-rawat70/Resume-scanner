import { useState } from "react";
import JDInput from "./components/JDInput.jsx";
import JDRequirements from "./components/JDRequirements.jsx";
import { matchResumes, parseJobDescription, uploadResumes } from "./api.js";

export default function App() {
  const [jd, setJd] = useState(null);      // parsed (and recruiter-edited) requirements
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resumeError, setResumeError] = useState("");
  const [candidates, setCandidates] = useState([]);
  const [matchResults, setMatchResults] = useState([]);
  const [matchingLoading, setMatchingLoading] = useState(false);
  const [matchError, setMatchError] = useState("");
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [activeTab, setActiveTab] = useState("jd");

  function sortMatchResults(results) {
    return [...results].sort((a, b) => (Number(b.overall_score) || 0) - (Number(a.overall_score) || 0));
  }

  function mergeCandidates(existing, incoming) {
    const keyOf = (candidate) => `${candidate.filename || ""}-${candidate.name || ""}-${candidate.email || ""}`;
    const map = new Map();

    [...existing, ...incoming].forEach((candidate) => {
      const key = keyOf(candidate);
      if (!key) return;
      map.set(key, candidate);
    });

    return Array.from(map.values());
  }

  async function handleExtract(input) {
    setLoading(true);
    setError("");
    try {
      setJd(await parseJobDescription(input));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleResumeUpload(event) {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;

    setResumeLoading(true);
    setResumeError("");
    try {
      const result = await uploadResumes(files);
      const nextCandidates = result.candidates || [];
      const mergedCandidates = mergeCandidates(candidates, nextCandidates);
      setCandidates(mergedCandidates);

      if (jd && mergedCandidates.length) {
        const ranking = await matchResumes({ jd, candidates: mergedCandidates });
        const nextResults = sortMatchResults(ranking.results || []);
        setMatchResults(nextResults);
        setSelectedCandidate(nextResults[0] || null);
        setActiveTab("ranking");
      } else {
        setMatchResults([]);
        setSelectedCandidate(null);
      }
    } catch (e) {
      setResumeError(e.message);
      setMatchResults([]);
      setSelectedCandidate(null);
    } finally {
      setResumeLoading(false);
      event.target.value = "";
    }
  }

  async function handleMatchResumes() {
    if (!jd || !candidates.length) {
      setMatchError("Add a parsed JD and upload candidate resumes first.");
      return;
    }

    setMatchingLoading(true);
    setMatchError("");
    try {
      const result = await matchResumes({ jd, candidates });
      const nextResults = sortMatchResults(result.results || []);
      setMatchResults(nextResults);
      setSelectedCandidate(nextResults[0] || null);
      setActiveTab("ranking");
    } catch (e) {
      setMatchError(e.message);
    } finally {
      setMatchingLoading(false);
    }
  }

  return (
    <div className="shell">
      <header className="topbar">
        <h1>Resume Matcher</h1>
        <ol className="steps" aria-label="Progress">
          {[
            { id: "jd", label: "Job description" },
            { id: "resumes", label: "Resumes" },
            { id: "ranking", label: "Ranking" },
          ].map((tab) => (
            <li key={tab.id} className={activeTab === tab.id ? "current" : ""}>
              <button
                type="button"
                className="step-button"
                onClick={() => setActiveTab(tab.id)}
                aria-pressed={activeTab === tab.id}
              >
                {tab.label}
              </button>
            </li>
          ))}
        </ol>
      </header>

      {activeTab === "jd" && (
        <main className="split">
          <JDInput onExtract={handleExtract} loading={loading} error={error} />
          <JDRequirements jd={jd} onChange={setJd} loading={loading} />
        </main>
      )}

      {activeTab === "resumes" && (
        <section className="panel" style={{ marginTop: 20 }}>
          <h2>Resume batch upload</h2>
          <p className="hint">Upload 10+ resumes in one batch. Supported formats: PDF and DOCX.</p>
          <input
            type="file"
            accept=".pdf,.docx"
            multiple
            onChange={handleResumeUpload}
            style={{ marginTop: 10, width: "100%" }}
          />
          {resumeLoading && <p className="muted">Processing resumes…</p>}
          {resumeError && <p className="error" role="alert">{resumeError}</p>}

          {candidates.length > 0 && (
            <div style={{ marginTop: 18 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                <h3 style={{ margin: 0 }}>Extracted candidates <span className="count">({candidates.length})</span></h3>
                <button className="secondary" onClick={handleMatchResumes} disabled={matchingLoading || !jd}>
                  {matchingLoading ? "Matching…" : "Match resumes"}
                </button>
              </div>
              <ul className="plain">
                {candidates.map((candidate) => (
                  <li key={candidate.filename || candidate.name || Math.random()}>
                    <button type="button" className="candidate-name-button" onClick={() => setSelectedCandidate((prev) => prev && prev.candidate_name === candidate.name ? prev : null)}>
                      <strong>{candidate.name || "Unnamed candidate"}</strong>
                    </button>
                    {candidate.email && <> — {candidate.email}</>}
                    {candidate.skills && candidate.skills.length > 0 && (
                      <div className="chips" style={{ marginTop: 6 }}>
                        {candidate.skills.slice(0, 6).map((skill) => (
                          <span key={skill} className="chip required">{skill}</span>
                        ))}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {activeTab === "ranking" && (
        <section className="panel" style={{ marginTop: 20 }}>
          {matchError && <p className="error" role="alert">{matchError}</p>}

          {!matchResults.length ? (
            <div className="panel empty">
              <h2>Ranking dashboard</h2>
              <p className="muted">Upload resumes and match them against the JD to see the ranking here.</p>
            </div>
          ) : (
            <div className="ranking-panel">
              <div className="ranking-header">
                <h3>Candidate ranking dashboard</h3>
                <div className="ranking-summary-badge" aria-label={`Matched candidates count ${matchResults.length}`}>
                  <span className="ranking-summary-label">Matched candidates</span>
                  <strong>{matchResults.length}</strong>
                </div>
              </div>
              <div className="table-wrap">
                <table className="ranking-table">
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Candidate</th>
                      <th>Experience</th>
                      <th>Match %</th>
                      <th>Matched Skills</th>
                    </tr>
                  </thead>
                  <tbody>
                    {matchResults.map((result, index) => (
                      <tr key={result.candidate_name} className={selectedCandidate && selectedCandidate.candidate_name === result.candidate_name ? "selected-row" : ""}>
                        <td><span className="rank-pill">#{index + 1}</span></td>
                        <td>
                          <button type="button" className="ranking-name-button" onClick={() => setSelectedCandidate(result)}>
                            {result.candidate_name}
                          </button>
                        </td>
                        <td>{result.candidate_experience_years != null && result.candidate_experience_years > 0 ? `${result.candidate_experience_years} years` : "Fresher"}</td>
                        <td>{Math.round(result.overall_score)}%</td>
                        <td>{result.matched_skills.length ? result.matched_skills.join(", ") : "None"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {selectedCandidate && (
                <div className="candidate-detail-card">
                  <h4>{selectedCandidate.candidate_name}</h4>
                  <div className="detail-grid">
                    <div>
                      <span className="detail-label">Overall match</span>
                      <strong>{Math.round(selectedCandidate.overall_score)}%</strong>
                    </div>
                    <div>
                      <span className="detail-label">Experience</span>
                      <strong>{selectedCandidate.candidate_experience_years != null && selectedCandidate.candidate_experience_years > 0 ? `${selectedCandidate.candidate_experience_years} years` : "Fresher"}</strong>
                    </div>
                    <div>
                      <span className="detail-label">Email</span>
                      <strong>{selectedCandidate.candidate_email || "Not provided"}</strong>
                    </div>
                    <div>
                      <span className="detail-label">Experience comparison</span>
                      <strong>{selectedCandidate.experience_comparison || "Not available"}</strong>
                    </div>
                  </div>

                  <div className="detail-section">
                    <h5>Matching skills</h5>
                    <div className="chips">
                      {selectedCandidate.matched_skills.length ? selectedCandidate.matched_skills.map((skill) => <span key={skill} className="chip required">{skill}</span>) : <span className="muted">None</span>}
                    </div>
                  </div>

                  <div className="detail-section">
                    <h5>Missing skills</h5>
                    <div className="chips">
                      {selectedCandidate.missing_skills.length ? selectedCandidate.missing_skills.map((skill) => <span key={skill} className="chip preferred">{skill}</span>) : <span className="muted">None</span>}
                    </div>
                  </div>

                  <div className="detail-section">
                    <h5>Why this score?</h5>
                    <ul className="plain reasons-list">
                      {selectedCandidate.reasons && selectedCandidate.reasons.length ? selectedCandidate.reasons.map((reason, index) => <li key={`${reason}-${index}`}>{reason}</li>) : <li>No explanation available.</li>}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
