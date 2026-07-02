import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API_BASE = "http://localhost:5003";

function App() {
  const [page, setPage] = useState("home");
  const [status, setStatus] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [loadingSubmissions, setLoadingSubmissions] = useState(false);

  const [mouse, setMouse] = useState({ x: 0, y: 0 });
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    fetchStatus();
    fetchSubmissions();

    const onMove = (event) => {
      setMouse({
        x: (event.clientX / window.innerWidth - 0.5) * 2,
        y: (event.clientY / window.innerHeight - 0.5) * 2
      });
    };

    const onScroll = () => setScrollY(window.scrollY);

    window.addEventListener("mousemove", onMove);
    window.addEventListener("scroll", onScroll);

    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("scroll", onScroll);
    };
  }, []);

  async function fetchStatus() {
    try {
      const response = await fetch(`${API_BASE}/api/status`);
      const data = await response.json();
      setStatus(data);
    } catch {
      setStatus(null);
    }
  }

  async function fetchSubmissions() {
    try {
      setLoadingSubmissions(true);
      const response = await fetch(`${API_BASE}/api/submissions`);
      const data = await response.json();
      setSubmissions(Array.isArray(data) ? data : []);
    } catch {
      setSubmissions([]);
    } finally {
      setLoadingSubmissions(false);
    }
  }

  async function openSubmission(id) {
    try {
      const response = await fetch(`${API_BASE}/api/submissions/${id}`);
      const data = await response.json();
      setSelectedSubmission(data);
      setPage("builder");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch {
      alert("Could not load submission.");
    }
  }

  return (
    <div className="app">
      <AnimatedBackground mouse={mouse} scrollY={scrollY} />

      <Navbar
        page={page}
        setPage={setPage}
        status={status}
        refreshSubmissions={fetchSubmissions}
      />

      <main>
        {page === "home" && (
          <HomePage
            setPage={setPage}
            mouse={mouse}
            scrollY={scrollY}
            status={status}
            submissions={submissions}
          />
        )}

        {page === "builder" && (
          <BuilderPage
            fetchSubmissions={fetchSubmissions}
            selectedSubmission={selectedSubmission}
            setSelectedSubmission={setSelectedSubmission}
          />
        )}

        {page === "dashboard" && (
          <DashboardPage
            submissions={submissions}
            loadingSubmissions={loadingSubmissions}
            fetchSubmissions={fetchSubmissions}
            openSubmission={openSubmission}
          />
        )}
      </main>
    </div>
  );
}

function AnimatedBackground({ mouse, scrollY }) {
  return (
    <div className="bgLayer" aria-hidden="true">
      <div
        className="orb orbOne"
        style={{
          transform: `translate3d(${mouse.x * 18}px, ${mouse.y * 18 + scrollY * 0.04}px, 0)`
        }}
      />
      <div
        className="orb orbTwo"
        style={{
          transform: `translate3d(${mouse.x * -24}px, ${mouse.y * -16 + scrollY * 0.02}px, 0)`
        }}
      />
      <div
        className="orb orbThree"
        style={{
          transform: `translate3d(${mouse.x * 12}px, ${mouse.y * -22 - scrollY * 0.03}px, 0)`
        }}
      />
      <div className="gridGlow" />
    </div>
  );
}

function Navbar({ page, setPage, status, refreshSubmissions }) {
  const navItems = [
    { id: "home", label: "Home" },
    { id: "builder", label: "Builder" },
    { id: "dashboard", label: "Dashboard" }
  ];

  function go(id) {
    setPage(id);
    if (id === "dashboard") refreshSubmissions();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <header className="navbar">
      <button className="brand" onClick={() => go("home")}>
        <span className="brandMark">T</span>
        <span>
          <strong>Talyrd</strong>
          <small>ATS Resume Studio</small>
        </span>
      </button>

      <nav>
        {navItems.map((item) => (
          <button
            key={item.id}
            className={page === item.id ? "active" : ""}
            onClick={() => go(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div className="statusPill">
        <span className={status?.backend === "ok" ? "dot live" : "dot"} />
        {status?.backend === "ok" ? "Live" : "Offline"}
      </div>
    </header>
  );
}

function HomePage({ setPage, mouse, scrollY, status, submissions }) {
  const stats = [
    { value: "1-page", label: "optimized resume output" },
    { value: "80%+", label: "ATS keyword target" },
    { value: "PDF", label: "LaTeX generated download" }
  ];

  return (
    <section className="homePage">
      <div className="hero">
        <div className="heroCopy">
          <div className="eyebrow">
            <span /> AI Resume Tailoring Engine
          </div>

          <h1>
            Turn your resume into a sharp, job-ready application.
          </h1>

          <p>
            Talyrd analyzes your resume against a job description, improves keyword
            alignment, generates a one-page LaTeX resume, and creates a matching
            cover letter.
          </p>

          <div className="heroActions">
            <button className="primaryBtn" onClick={() => setPage("builder")}>
              Start Building
            </button>
            <button className="secondaryBtn" onClick={() => setPage("dashboard")}>
              View Dashboard
            </button>
          </div>

          <div className="heroStats">
            {stats.map((stat) => (
              <div key={stat.label}>
                <strong>{stat.value}</strong>
                <span>{stat.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div
          className="heroVisual"
          style={{
            transform: `translate3d(${mouse.x * 8}px, ${mouse.y * 8 + scrollY * 0.02}px, 0)`
          }}
        >
          <div className="resumeMock">
            <div className="mockHeader">
              <div>
                <strong>Anvesh Varma</strong>
                <span>Software Engineer</span>
              </div>
              <em>ATS 86%</em>
            </div>

            <div className="mockSection wide" />
            <div className="mockSection short" />

            <div className="mockTitle">Experience</div>
            <div className="mockLine" />
            <div className="mockLine medium" />
            <div className="mockLine small" />

            <div className="mockTitle">Skills</div>
            <div className="chipRow">
              <span>Python</span>
              <span>AWS</span>
              <span>Docker</span>
              <span>FastAPI</span>
            </div>
          </div>

          <div className="floatingCard cardA">
            <strong>+42%</strong>
            <span>keyword coverage</span>
          </div>

          <div className="floatingCard cardB">
            <strong>PDF</strong>
            <span>ready to apply</span>
          </div>
        </div>
      </div>

      <section className="featureGrid">
        <FeatureCard
          number="01"
          title="Analyze"
          description="Extract resume text and compare it against the target job description."
        />
        <FeatureCard
          number="02"
          title="Tailor"
          description="Rewrite content with relevant keywords while preserving truthful experience."
        />
        <FeatureCard
          number="03"
          title="Generate"
          description="Create a compact one-page LaTeX resume and matching cover letter."
        />
      </section>

      <section className="processPanel">
        <div>
          <span className="eyebrowText">Workflow</span>
          <h2>From upload to polished PDF in one flow.</h2>
        </div>

        <div className="timeline">
          {["Upload Resume", "Paste Job Description", "Analyze ATS Gaps", "Generate PDF"].map((item, index) => (
            <div className="timelineItem" key={item}>
              <span>{index + 1}</span>
              <p>{item}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="miniDashboard">
        <div>
          <span className="eyebrowText">System</span>
          <h2>Current workspace</h2>
        </div>

        <div className="miniCards">
          <InfoCard label="Backend" value={status?.backend || "checking"} />
          <InfoCard label="OpenAI" value={status?.openai || "checking"} />
          <InfoCard label="Submissions" value={String(submissions.length)} />
        </div>
      </section>
    </section>
  );
}

function FeatureCard({ number, title, description }) {
  return (
    <article className="featureCard">
      <span>{number}</span>
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}

function InfoCard({ label, value }) {
  return (
    <div className="infoCard">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function BuilderPage({ fetchSubmissions, selectedSubmission, setSelectedSubmission }) {
  const [form, setForm] = useState({
    fullName: "Anvesh Varma Dantuluri",
    targetRole: "Software Engineer",
    jobDescription: ""
  });
  const [resumeFile, setResumeFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    if (!resumeFile) {
      setUploadError("Please upload a resume file.");
      return;
    }

    setIsUploading(true);
    setUploadError("");

    const formData = new FormData();
    formData.append("full_name", form.fullName);
    formData.append("target_role", form.targetRole);
    formData.append("job_description", form.jobDescription);
    formData.append("resume", resumeFile);

    try {
      const response = await fetch(`${API_BASE}/api/uploads`, {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Upload failed");
      }

      setSelectedSubmission(data);
      await fetchSubmissions();
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (error) {
      setUploadError(error.message || "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  const score = selectedSubmission?.post_ats_score || selectedSubmission?.ats_score || 0;

  return (
    <section className="builderPage pageShell">
      <div className="pageHeader">
        <div>
          <span className="eyebrowText">Builder</span>
          <h1>Generate your tailored resume.</h1>
          <p>
            Upload your resume, paste the job description, and Talyrd will generate
            an ATS-optimized one-page PDF.
          </p>
        </div>

        <ScoreRing score={score} />
      </div>

      <div className="builderGrid">
        <form className="glassPanel uploadForm" onSubmit={handleSubmit}>
          <label>
            Full Name
            <input
              value={form.fullName}
              onChange={(event) => setForm({ ...form, fullName: event.target.value })}
              placeholder="Your full name"
            />
          </label>

          <label>
            Target Role
            <input
              value={form.targetRole}
              onChange={(event) => setForm({ ...form, targetRole: event.target.value })}
              placeholder="Software Engineer"
            />
          </label>

          <label>
            Resume File
            <div className="fileDrop">
              <input
                type="file"
                accept=".pdf,.docx,.txt,.tex"
                onChange={(event) => setResumeFile(event.target.files?.[0] || null)}
              />
              <strong>{resumeFile ? resumeFile.name : "Drop or choose resume"}</strong>
              <span>PDF, DOCX, TXT, or TEX</span>
            </div>
          </label>

          <label>
            Job Description
            <textarea
              value={form.jobDescription}
              onChange={(event) => setForm({ ...form, jobDescription: event.target.value })}
              placeholder="Paste the full job description here..."
            />
          </label>

          {uploadError && <div className="errorBox">{uploadError}</div>}

          <button className="primaryBtn full" disabled={isUploading}>
            {isUploading ? "Generating..." : "Generate Tailored Resume"}
          </button>

          {isUploading && (
            <div className="loadingStack">
              <div />
              <div />
              <div />
              <span>Analyzing resume, improving ATS coverage, compiling PDF...</span>
            </div>
          )}
        </form>

        <ResultPanel submission={selectedSubmission} />
      </div>
    </section>
  );
}

function ScoreRing({ score }) {
  const safeScore = Math.max(0, Math.min(100, Number(score) || 0));

  return (
    <div className="scoreRing" style={{ "--score": `${safeScore * 3.6}deg` }}>
      <div>
        <strong>{safeScore}%</strong>
        <span>ATS Score</span>
      </div>
    </div>
  );
}

function ResultPanel({ submission }) {
  const keywordList = submission?.matched_keywords || [];
  const missingList = submission?.missing_keywords || [];
  const sections = submission?.tailored_sections;

  if (!submission) {
    return (
      <aside className="glassPanel resultPanel emptyState">
        <div className="emptyIcon">✦</div>
        <h2>Your result will appear here</h2>
        <p>
          Once generated, you’ll see ATS score, matched keywords, missing keywords,
          resume sections, and download links.
        </p>
      </aside>
    );
  }

  return (
    <aside className="glassPanel resultPanel">
      <div className="resultTop">
        <div>
          <span className="eyebrowText">Generated</span>
          <h2>{submission.target_role}</h2>
          <p>{submission.original_filename}</p>
        </div>
        <ScoreRing score={submission.post_ats_score || submission.ats_score} />
      </div>

      <div className="downloadRow">
        {submission.resume_pdf_url && (
          <a href={`${API_BASE}${submission.resume_pdf_url}`} target="_blank">
            Open Resume PDF
          </a>
        )}
        {submission.cover_letter_pdf_url && (
          <a href={`${API_BASE}${submission.cover_letter_pdf_url}`} target="_blank">
            Open Cover Letter
          </a>
        )}
      </div>

      <div className="scoreCompare">
        <div>
          <span>Before</span>
          <strong>{submission.pre_ats_score ?? 0}%</strong>
        </div>
        <div>
          <span>After</span>
          <strong>{submission.post_ats_score ?? submission.ats_score ?? 0}%</strong>
        </div>
      </div>

      <KeywordBlock title="Matched Keywords" items={keywordList} positive />
      <KeywordBlock title="Remaining Keywords" items={missingList} />

      {sections && (
        <div className="sectionPreview">
          <h3>Resume Sections</h3>
          <PreviewSection title="Summary" value={sections.summary} />
          <PreviewSection title="Skills" value={(sections.skills || []).join(", ")} />
          <PreviewSection title="Experience" value={(sections.experience || []).slice(0, 4).join(" • ")} />
          <PreviewSection title="Projects" value={(sections.projects || []).slice(0, 3).join(" • ")} />
          <PreviewSection title="Education" value={(sections.education || []).join(" • ")} />
        </div>
      )}
    </aside>
  );
}

function KeywordBlock({ title, items, positive }) {
  return (
    <div className="keywordBlock">
      <h3>{title}</h3>
      <div className="tags">
        {(items || []).slice(0, 24).map((item) => (
          <span className={positive ? "goodTag" : ""} key={item}>
            {item}
          </span>
        ))}
        {(!items || items.length === 0) && <small>No keywords to show.</small>}
      </div>
    </div>
  );
}

function PreviewSection({ title, value }) {
  if (!value) return null;

  return (
    <div className="previewSection">
      <strong>{title}</strong>
      <p>{value}</p>
    </div>
  );
}

function DashboardPage({ submissions, loadingSubmissions, fetchSubmissions, openSubmission }) {
  return (
    <section className="dashboardPage pageShell">
      <div className="pageHeader">
        <div>
          <span className="eyebrowText">Dashboard</span>
          <h1>Your generated resumes.</h1>
          <p>Review previous runs, compare scores, and reopen generated PDFs.</p>
        </div>

        <button className="secondaryBtn" onClick={fetchSubmissions}>
          Refresh
        </button>
      </div>

      {loadingSubmissions ? (
        <div className="glassPanel loadingDashboard">Loading submissions...</div>
      ) : submissions.length === 0 ? (
        <div className="glassPanel emptyDashboard">
          <h2>No submissions yet</h2>
          <p>Generate your first tailored resume from the Builder page.</p>
        </div>
      ) : (
        <div className="submissionGrid">
          {submissions.map((submission) => (
            <article className="submissionCard" key={submission.id}>
              <div className="cardHeader">
                <div>
                  <span>#{submission.id}</span>
                  <h3>{submission.target_role}</h3>
                </div>
                <ScoreBadge score={submission.post_ats_score || submission.ats_score} />
              </div>

              <p>{submission.original_filename}</p>

              <div className="cardMeta">
                <span>Before: {submission.pre_ats_score ?? 0}%</span>
                <span>After: {submission.post_ats_score ?? submission.ats_score ?? 0}%</span>
              </div>

              <div className="cardActions">
                <button onClick={() => openSubmission(submission.id)}>Inspect</button>
                {submission.resume_pdf_url && (
                  <a href={`${API_BASE}${submission.resume_pdf_url}`} target="_blank">
                    PDF
                  </a>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function ScoreBadge({ score }) {
  const value = Number(score) || 0;

  return (
    <div className={value >= 80 ? "scoreBadge high" : "scoreBadge"}>
      {value}%
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
