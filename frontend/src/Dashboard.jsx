import { useEffect, useState } from "react";
import { getLandmarks, getStats } from "./api.js";

export default function Dashboard({ onNavigate }) {
  const [places, setPlaces] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getLandmarks().catch(() => []),
      getStats().catch(() => ({ tts_calls: 0, stt_calls: 0, total_characters: 0 })),
    ]).then(([p, s]) => {
      setPlaces(p);
      setStats(s);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner" />
        <span className="loading-text">Loading dashboard…</span>
      </div>
    );
  }

  return (
    <>
      {/* Stats Row */}
      <div className="stats-grid">
        <div className="stat-card amber">
          <div className="stat-icon">🏛️</div>
          <div className="stat-label">Landmarks</div>
          <div className="stat-value">{places.length}</div>
          <div className="stat-change up">Active in KB</div>
        </div>
        <div className="stat-card emerald">
          <div className="stat-icon">🗣️</div>
          <div className="stat-label">TTS Calls</div>
          <div className="stat-value">{stats?.tts_calls || 0}</div>
          <div className="stat-change up">This session</div>
        </div>
        <div className="stat-card blue">
          <div className="stat-icon">🎤</div>
          <div className="stat-label">STT Calls</div>
          <div className="stat-value">{stats?.stt_calls || 0}</div>
          <div className="stat-change up">This session</div>
        </div>
        <div className="stat-card violet">
          <div className="stat-icon">✦</div>
          <div className="stat-label">Characters Used</div>
          <div className="stat-value">{(stats?.total_characters || 0).toLocaleString()}</div>
          <div className="stat-change up">ElevenLabs quota</div>
        </div>
      </div>

      {/* Landmark Preview Cards */}
      <div className="section-header">
        <div>
          <div className="section-title">Explore Landmarks</div>
          <div className="section-subtitle">Click a landmark to start narration</div>
        </div>
      </div>

      <div className="landmark-grid">
        {places.map((p) => (
          <div
            key={p.id}
            className="landmark-card"
            onClick={() => onNavigate("guide")}
          >
            <div className="landmark-img-wrap">
              <img src={p.image || "/images/bara_imambara.jpg"} alt={p.title} loading="lazy" />
              <div className="landmark-img-overlay" />
              <span className="landmark-badge">{p.category || "Landmark"}</span>
            </div>
            <div className="landmark-info">
              <div className="landmark-title">{p.title}</div>
              <div className="landmark-desc">{p.description || "Explore this landmark with AI-powered narration."}</div>
              <div className="landmark-meta">
                <span className="landmark-meta-item">
                  <span className="star">★</span> {p.rating || "4.5"}
                </span>
                <span className="landmark-meta-item">📅 Est. {p.era || "Historic"}</span>
                <span className="landmark-meta-item">👥 {p.visitors || "Popular"}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="section-header">
        <div>
          <div className="section-title">Quick Actions</div>
          <div className="section-subtitle">Jump into a feature</div>
        </div>
      </div>

      <div className="stats-grid" style={{ gridTemplateColumns: "repeat(2, 1fr)" }}>
        <div
          className="stat-card amber"
          style={{ cursor: "pointer" }}
          onClick={() => onNavigate("guide")}
        >
          <div className="stat-icon">🎧</div>
          <div className="stat-label">AI Guide</div>
          <div className="stat-value" style={{ fontSize: 18 }}>Start Narration</div>
          <div className="stat-change up">Pick a landmark & listen</div>
        </div>
        <div
          className="stat-card emerald"
          style={{ cursor: "pointer" }}
          onClick={() => onNavigate("interp")}
        >
          <div className="stat-icon">🌐</div>
          <div className="stat-label">Interpreter</div>
          <div className="stat-value" style={{ fontSize: 18 }}>Live Translation</div>
          <div className="stat-change up">English ⇄ Hindi</div>
        </div>
      </div>
    </>
  );
}
