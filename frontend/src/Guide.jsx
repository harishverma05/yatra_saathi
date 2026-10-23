import { useEffect, useRef, useState } from "react";
import MicButton from "./MicButton.jsx";
import { ask, getLandmarks, narrate } from "./api.js";

export default function Guide() {
  const [places, setPlaces] = useState([]);
  const [active, setActive] = useState(null);
  const [lang, setLang] = useState("hi");
  const [busy, setBusy] = useState(false);
  const [story, setStory] = useState(null);
  const [qa, setQa] = useState(null);
  const [error, setError] = useState("");
  const audio = useRef(null);

  useEffect(() => {
    getLandmarks().then(setPlaces).catch((e) => setError(e.message));
  }, []);

  const play = (url) => {
    audio.current?.pause();
    audio.current = new Audio(url);
    audio.current.play();
  };

  const pick = async (id, l = lang) => {
    setActive(id);
    setQa(null);
    setStory(null);
    setBusy(true);
    setError("");
    try {
      const r = await narrate(id, l);
      setStory(r);
      play(r.audio_url);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const onAudio = async (blob) => {
    setBusy(true);
    setError("");
    try {
      const r = await ask(blob, active, lang);
      setQa(r);
      play(r.audio_url);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const switchLang = (l) => {
    setLang(l);
    if (active) pick(active, l);
  };

  const activeLandmark = places.find((p) => p.id === active);

  return (
    <>
      {/* Language Switch */}
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 20 }}>
        <div className="lang-switch">
          {[
            { code: "hi", label: "हिन्दी" },
            { code: "en", label: "English" },
          ].map((l) => (
            <button
              key={l.code}
              className={`lang-btn ${lang === l.code ? "active" : ""}`}
              onClick={() => switchLang(l.code)}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      {/* Landmark Selection */}
      <div className="section-header">
        <div>
          <div className="section-title">Choose a Landmark</div>
          <div className="section-subtitle">Select to hear its story</div>
        </div>
      </div>

      <div className="landmark-grid">
        {places.map((p) => (
          <div
            key={p.id}
            className={`landmark-card ${active === p.id ? "selected" : ""}`}
            onClick={() => pick(p.id)}
          >
            <div className="landmark-img-wrap">
              <img src={p.image || "/images/bara_imambara.jpg"} alt={p.title} loading="lazy" />
              <div className="landmark-img-overlay" />
              <span className="landmark-badge">{p.category || "Landmark"}</span>
            </div>
            <div className="landmark-info">
              <div className="landmark-title">{p.title}</div>
              <div className="landmark-desc">{p.description || "Tap to explore"}</div>
              <div className="landmark-meta">
                <span className="landmark-meta-item">
                  <span className="star">★</span> {p.rating || "4.5"}
                </span>
                <span className="landmark-meta-item">📅 Est. {p.era || "Historic"}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Loading State */}
      {busy && !story && (
        <div className="loading-spinner">
          <div className="spinner" />
          <span className="loading-text">Generating narration…</span>
        </div>
      )}

      {/* Narration Story Panel */}
      {story && (
        <div className="story-panel">
          <div className="story-header">
            <span className="story-label">
              🎧 {activeLandmark?.title || "Narration"} — {lang === "hi" ? "हिन्दी" : "English"}
            </span>
            <button className="replay-btn" onClick={() => play(story.audio_url)}>
              ▶ Replay
            </button>
          </div>
          <p className="story-text">{story.text}</p>
        </div>
      )}

      {/* Ask a Question */}
      {active && (
        <MicButton onAudio={onAudio} busy={busy} label="Ask a question" />
      )}

      {/* Q&A Bubble */}
      {qa && (
        <div className="qa-bubble">
          <div className="qa-question">"{qa.question}"</div>
          <p className="qa-answer">{qa.text}</p>
          <button className="replay-btn" style={{ marginTop: 10 }} onClick={() => play(qa.audio_url)}>
            ▶ Replay answer
          </button>
        </div>
      )}

      {error && <p className="error-msg">{error}</p>}
    </>
  );
}
