import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import "./style.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5003";

function App() {
  const [status, setStatus] = useState(null);
  const [fullName, setFullName] = useState("Anvesh Varma Dantuluri");
  const [targetRole, setTargetRole] = useState("Software Engineer");
  const [jobDescription, setJobDescription] = useState("");
  const [resumeFile, setResumeFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadStatus = async () => {
    const response = await axios.get(`${API_URL}/api/status`);
    setStatus(response.data);
  };

  const loadSubmissions = async () => {
    const response = await axios.get(`${API_URL}/api/submissions`);
    setSubmissions(response.data);
  };

  const loadSubmissionDetails = async (id) => {
    const response = await axios.get(`${API_URL}/api/submissions/${id}`);
    setSelectedSubmission(response.data);
  };

  const uploadResume = async () => {
    if (!resumeFile) {
      setUploadResult({ error: "Please select a resume file." });
      return;
    }

    setLoading(true);
    setUploadResult(null);
    setSelectedSubmission(null);

    const formData = new FormData();
    formData.append("full_name", fullName);
    formData.append("target_role", targetRole);
    formData.append("job_description", jobDescription);
    formData.append("resume", resumeFile);

    try {
      const response = await axios.post(`${API_URL}/api/uploads`, formData);
      setUploadResult(response.data);
      await loadSubmissions();
      await loadSubmissionDetails(response.data.submission_id);
    } catch (error) {
      setUploadResult({
        error: error.response?.data?.error || "Upload failed."
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    loadSubmissions();
  }, []);

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">AI Resume Builder</p>
        <h1>Talyrd</h1>
        <p>
          Upload your resume, analyze ATS gaps, generate tailored content with
          OpenAI, and export resume plus cover letter PDFs.
        </p>
      </section>

      <section className="statusBar">
        {status ? (
          <>
            <span>Backend: {status.backend}</span>
            <span>Database: {status.database}</span>
            <span>OpenAI: {status.openai}</span>
            <span>PDF: {status.pdf_generation}</span>
            <span>Version: {status.version}</span>
          </>
        ) : (
          <span>Loading system status...</span>
        )}
      </section>

      <section className="layout">
        <div className="card">
          <p className="eyebrow dark">Step 8</p>
          <h2>Generate Resume PDFs</h2>

          <label>Full Name</label>
          <input
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
          />

          <label>Target Role</label>
          <input
            value={targetRole}
            onChange={(event) => setTargetRole(event.target.value)}
          />

          <label>Resume File</label>
          <input
            type="file"
            accept=".pdf,.docx,.txt,.tex"
            onChange={(event) => setResumeFile(event.target.files[0])}
          />

          <label>Job Description</label>
          <textarea
            placeholder="Paste the job description here..."
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
          />

          <button onClick={uploadResume} disabled={loading}>
            {loading ? "Generating PDFs..." : "Generate Tailored PDFs"}
          </button>

          {uploadResult?.error && (
            <p className="error">{uploadResult.error}</p>
          )}

          {uploadResult && !uploadResult.error && (
            <div className="successBox">
              <strong>{uploadResult.message}</strong>
              <p>Submission ID: {uploadResult.submission_id}</p>
              <p>Before ATS: {uploadResult.pre_ats_score}%</p>
              <p>After ATS: {uploadResult.post_ats_score}%</p>
              <p>PDF Status: {uploadResult.pdf_status}</p>

              <div className="linkRow">
                <a
                  href={`${API_URL}${uploadResult.resume_pdf_url}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open Resume PDF
                </a>

                <a
                  href={`${API_URL}${uploadResult.cover_letter_pdf_url}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open Cover Letter PDF
                </a>
              </div>
            </div>
          )}
        </div>

        <div className="card">
          <p className="eyebrow dark">Output</p>
          <h2>Tailored Result</h2>

          {!selectedSubmission && <p>No tailored result selected yet.</p>}

          {selectedSubmission && (
            <>
              <div className="scoreGrid">
                <div>
                  <span>Before</span>
                  <strong>{selectedSubmission.pre_ats_score}%</strong>
                </div>
                <div>
                  <span>After</span>
                  <strong>{selectedSubmission.post_ats_score}%</strong>
                </div>
              </div>

              <div className="metaGrid">
                <div>
                  <span>Tailoring</span>
                  <strong>{selectedSubmission.tailoring_status}</strong>
                </div>
                <div>
                  <span>PDF</span>
                  <strong>{selectedSubmission.pdf_status}</strong>
                </div>
              </div>

              {selectedSubmission.resume_pdf_url && (
                <div className="linkRow topLinks">
                  <a
                    href={`${API_URL}${selectedSubmission.resume_pdf_url}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open Resume PDF
                  </a>

                  <a
                    href={`${API_URL}${selectedSubmission.cover_letter_pdf_url}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open Cover Letter PDF
                  </a>
                </div>
              )}

              <h3>Matched Keywords</h3>
              <div className="tags">
                {selectedSubmission.matched_keywords.map((keyword) => (
                  <span key={keyword}>{keyword}</span>
                ))}
              </div>

              <h3>Missing Keywords</h3>
              <div className="tags missing">
                {selectedSubmission.missing_keywords.map((keyword) => (
                  <span key={keyword}>{keyword}</span>
                ))}
              </div>

              <h3>Improvement Summary</h3>
              <div className="textPanel">
                {selectedSubmission.improvement_summary || "No summary available."}
              </div>

              <h3>Tailored Resume Text</h3>
              <pre className="previewBox light">
                {selectedSubmission.tailored_resume_text}
              </pre>

              <h3>Cover Letter Text</h3>
              <pre className="previewBox light">
                {selectedSubmission.cover_letter_text}
              </pre>
            </>
          )}
        </div>
      </section>

      <section className="card historyCard">
        <p className="eyebrow dark">History</p>
        <h2>Submissions</h2>

        <div className="history">
          {submissions.length === 0 && <p>No submissions yet.</p>}

          {submissions.map((item) => (
            <button
              className="historyItem"
              key={item.id}
              onClick={() => loadSubmissionDetails(item.id)}
            >
              <div>
                <strong>{item.original_filename}</strong>
                <p>{item.full_name}</p>
                <p>{item.target_role}</p>
                <small>
                  Before {item.pre_ats_score}% · After {item.post_ats_score}% ·{" "}
                  PDF {item.pdf_status || "pending"} · {item.created_at}
                </small>
              </div>
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
