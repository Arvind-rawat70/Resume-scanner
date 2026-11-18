import { useState } from "react";

const years = (e) => {
  if (e.min_years == null) return "Fresher";
  if (e.max_years) return `${e.min_years}–${e.max_years} years`;
  return `${e.min_years}+ years`;
};

function SkillChip({ skill, onToggle, onRemove }) {
  const required = skill.importance === "required";
  return (
    <span className={required ? "chip required" : "chip preferred"}>
      <button className="chip-label" onClick={onToggle}
              title={`${skill.evidence}\n\nClick to make ${required ? "preferred" : "required"}`}>
        {skill.name}
      </button>
      <button className="chip-x" onClick={onRemove} aria-label={`Remove ${skill.name}`}>×</button>
    </span>
  );
}

export default function JDRequirements({ jd, onChange, loading }) {
  const [newSkill, setNewSkill] = useState("");

  if (!jd) {
    return (
      <section className="panel empty" aria-live="polite">
        <h2>Extracted requirements</h2>
        <p className="muted">
          {loading ? "Reading the job description…"
                   : "Add a job description and select Extract requirements. Skills, experience and education will appear here for you to review."}
        </p>
      </section>
    );
  }

  const update = (patch) => onChange({ ...jd, ...patch });
  const toggle = (name) => update({ skills: jd.skills.map((s) =>
    s.name === name ? { ...s, importance: s.importance === "required" ? "preferred" : "required" } : s) });
  const remove = (name) => update({ skills: jd.skills.filter((s) => s.name !== name) });
  const add = () => {
    const name = newSkill.trim();
    if (!name || jd.skills.some((s) => s.name.toLowerCase() === name.toLowerCase())) return setNewSkill("");
    update({ skills: [...jd.skills, { name, category: "Added manually", importance: "required", evidence: "Added by recruiter" }] });
    setNewSkill("");
  };

  const required = jd.skills.filter((s) => s.importance === "required");
  const preferred = jd.skills.filter((s) => s.importance === "preferred");
  const e = jd.experience;

  return (
    <section className="panel" aria-live="polite">
      <h2>Extracted requirements</h2>

      <div className="role">
        <p className="role-title">{jd.title || "Untitled role"}</p>
        <p className="muted">{jd.summary}</p>
      </div>

      <dl className="facts">
        <div><dt>Experience</dt><dd>{years(e)}</dd></div>
        <div><dt>Level</dt><dd>{e.seniority || "Fresher"}</dd></div>
      </dl>

      {jd.education.length > 0 && (
        <>
          <h3>Education</h3>
          <ul className="plain">
            {jd.education.map((d, i) => (
              <li key={`${d.level}-${i}`}>
                {d.level}{d.fields.length ? ` in ${d.fields.join(", ")}` : ""}
                {!d.required && <em className="muted"> (preferred)</em>}
              </li>
            ))}
          </ul>
        </>
      )}

      {(jd.certifications.length > 0 || e.min_years != null || e.seniority) && (
        <>
          <h3>Eligibility</h3>
          <ul className="plain">
            {e.min_years != null && <li>Minimum experience: {years(e)}</li>}
            {e.seniority && <li>Seniority: {e.seniority}</li>}
            {jd.certifications.length > 0 && <li>Certifications: {jd.certifications.join(", ")}</li>}
          </ul>
        </>
      )}

      <h3>Required skills <span className="count">{required.length}</span></h3>
      <div className="chips">
        {required.map((s) => <SkillChip key={s.name} skill={s} onToggle={() => toggle(s.name)} onRemove={() => remove(s.name)} />)}
        {!required.length && <span className="muted">None found</span>}
      </div>

      <h3>Preferred skills <span className="count">{preferred.length}</span></h3>
      <div className="chips">
        {preferred.map((s) => <SkillChip key={s.name} skill={s} onToggle={() => toggle(s.name)} onRemove={() => remove(s.name)} />)}
        {!preferred.length && <span className="muted">None found</span>}
      </div>

      <div className="add-skill">
        <input value={newSkill} onChange={(ev) => setNewSkill(ev.target.value)}
               onKeyDown={(ev) => ev.key === "Enter" && add()}
               placeholder="Missing a skill? Add it" aria-label="Add a skill" />
        <button className="secondary" onClick={add}>Add skill</button>
      </div>
      <p className="hint">Hover a skill to see the sentence it came from. Click a skill to switch it between required and preferred.</p>

      {jd.responsibilities.length > 0 && (<>
        <h3>Responsibilities</h3>
        <ul className="plain">{jd.responsibilities.map((r, i) => <li key={i}>{r}</li>)}</ul>
      </>)}

      {jd.soft_skills.length > 0 && (<>
        <h3>Soft skills</h3>
        <div className="chips">{jd.soft_skills.map((s) => <span key={s} className="chip soft"><span className="chip-label static">{s}</span></span>)}</div>
      </>)}
    </section>
  );
}
