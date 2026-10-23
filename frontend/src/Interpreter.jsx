import { useState } from "react";
import MicButton from "./MicButton.jsx";
import { interpret } from "./api.js";

export default function Interpreter() {
  const [mode, setMode] = useState("auto"); // "auto", "en", "hi"
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState([]);
  const [error, setError] = useState("");
  const [lastSpeaker, setLastSpeaker] = useState(null);

  const onAudio = async (blob) => {
    setBusy(true);
    setError("");
    try {
      const src = mode === "auto" ? "auto" : mode;
      const tgt = mode === "auto" ? "auto" : mode === "en" ? "hi" : "en";
      const r = await interpret(blob, src, tgt);
      setLastSpeaker(r.speaker || (r.src === "en" ? "Tourist (English)" : "Local (हिन्दी)"));
      setLog((l) => [r, ...l]);
      if (r.audio_url) {
        new Audio(r.audio_url).play();
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="interpreter-container">
      {/* Header Bar */}
      <div className="interp-topbar">
        <div>
          <h2 className="interp-heading">Live Interpreter</h2>
          <p className="interp-subheading">
            Automatic bilingual speech-to-speech translation powered by ElevenLabs
          </p>
        </div>
        <div className="interp-badge">
          <span className="dot" /> Outlined steps use ElevenLabs
        </div>
      </div>



      {/* Mode Controls */}
      <div className="interp-controls">
        <div className="mode-toggle-group">
          <button
            className={`mode-btn ${mode === "auto" ? "active" : ""}`}
            onClick={() => setMode("auto")}
          >
            ⚡ Auto-Detect & Translate
          </button>
          <button
            className={`mode-btn ${mode === "en" ? "active" : ""}`}
            onClick={() => setMode("en")}
          >
            Tourist (English ➔ हिन्दी)
          </button>
          <button
            className={`mode-btn ${mode === "hi" ? "active" : ""}`}
            onClick={() => setMode("hi")}
          >
            Local (हिन्दी ➔ English)
          </button>
        </div>

        <p className="interp-hint">
          {mode === "auto"
            ? "Speak in either English or Hindi — the system automatically identifies who spoke and translates to the other person!"
            : mode === "en"
              ? "Tourist Mode: Speak in English → Translated voice plays in Hindi for the local."
              : "Local Mode: Speak in Hindi → Translated voice plays in English for the tourist."}
        </p>

        <MicButton
          onAudio={onAudio}
          busy={busy}
          label={
            mode === "auto"
              ? "Tap to Speak (Auto-Detect)"
              : mode === "en"
                ? "Tourist: Speak English"
                : "Local: हिन्दी में बोलें"
          }
        />

        {error && <p className="error-msg">{error}</p>}
      </div>

      {/* Translation Feed */}
      {log.length > 0 && (
        <div className="history-section">
          <div className="section-header">
            <div>
              <div className="section-title">Live Conversation Stream</div>
              <div className="section-subtitle">
                {log.length} bidirectional dialogue turn{log.length > 1 ? "s" : ""}
              </div>
            </div>
          </div>

          <ul className="translation-log">
            {log.map((m, i) => {
              const isTourist = m.speaker?.includes("Tourist") || m.src === "en";
              return (
                <li
                  key={i}
                  className={`translation-item ${isTourist ? "tourist-bubble" : "local-bubble"}`}
                >
                  <div className="dialogue-meta">
                    <span className={`speaker-tag ${isTourist ? "tourist-tag" : "local-tag"}`}>
                      {isTourist ? "🗣️ Tourist Speaks" : "🏛️ Local Speaks"}
                    </span>
                    <span className="lang-route-tag">
                      {m.src === "en" ? "English ➔ हिन्दी" : "हिन्दी ➔ English"}
                    </span>
                  </div>

                  <div className="dialogue-original">
                    <span className="dialogue-label">Heard:</span>
                    <span className="dialogue-quote">“{m.text}”</span>
                  </div>

                  <div className="dialogue-translated">
                    <span className="dialogue-label">Translated Voice:</span>
                    <span className="dialogue-quote">“{m.translation}”</span>
                  </div>

                  {m.audio_url && (
                    <button
                      className="translation-replay"
                      onClick={() => new Audio(m.audio_url).play()}
                    >
                      ▶ Replay Translated Speech
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
