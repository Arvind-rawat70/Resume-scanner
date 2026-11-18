// Thin API client. Later modules add uploadResumes(), rankCandidates(), etc.
async function request(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try { detail = (await res.json()).detail || detail; } catch { /* non-JSON error */ }
    throw new Error(detail);
  }
  return res.json();
}

export function parseJobDescription({ text, file }) {
  const body = new FormData();
  if (file) body.append("file", file);
  else body.append("text", text);
  return request("/api/jd/parse", { method: "POST", body });
}

export function uploadResumes(files) {
  const body = new FormData();
  files.forEach((file) => body.append("files", file));
  return request("/api/resumes/upload", { method: "POST", body });
}

export function matchResumes({ jd, candidates }) {
  return request("/api/match/resumes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jd, candidates }),
  });
}
