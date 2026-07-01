import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import "./style.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5003";

function App() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");

  const loadStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/status`);
      setStatus(response.data);
      setError("");
    } catch (err) {
      setError("Frontend could not connect to backend API.");
      setStatus(null);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">AI Resume Builder</p>
        <h1>Talyrd</h1>
        <p>
          Full-stack resume tailoring platform using React, Flask, Docker,
          PostgreSQL, OpenAI, and LaTeX.
        </p>
      </section>

      <section className="card">
        <div className="cardHeader">
          <div>
            <p className="eyebrow dark">System Check</p>
            <h2>Application Status</h2>
          </div>

          <button onClick={loadStatus}>Refresh</button>
        </div>

        {error && <p className="error">{error}</p>}

        {!error && !status && <p>Loading backend status...</p>}

        {status && (
          <div className="statusGrid">
            <div className="statusItem">
              <span>App</span>
              <strong>{status.app}</strong>
            </div>

            <div className="statusItem">
              <span>Version</span>
              <strong>{status.version}</strong>
            </div>

            <div className="statusItem">
              <span>Backend</span>
              <strong>{status.backend}</strong>
            </div>

            <div className="statusItem">
              <span>Database</span>
              <strong>{status.database}</strong>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
