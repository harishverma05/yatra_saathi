import { useState } from "react";
import MicButton from "./MicButton.jsx";
import { interpret } from "./api.js";

const NAMES = { en: "English", hi: "हिन्दी" };

export default function Interpreter() {
  const [src, setSrc] = useState("en");
  const tgt = src === "en" ? "hi" : "en";
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState([]);
  const [error, setError] = useState("");

  const onAudio = async (blob) => {
    setBusy(true);
    setError("");
    try {
      const r = await interpret(blob, src, tgt);
      setLog((l) => [{ ...r, src, tgt }, ...l]);
      new Audio(r.audio_url).play();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      {/* Language Pair Header */}
      <div className="interpreter-header">
        <div className="lang-pill">{NAMES[src]}</div>
        <button
          className="swap-btn"
          onClick={() => setSrc(tgt)}
          aria-label="Swap languages"
        >
          ⇄
        </button>
        <div className="lang-pill">{NAMES[tgt]}</div>
      </div>

      <p className="interp-hint">
        Speak in {NAMES[src]} → the other person hears {NAMES[tgt]}
      </p>

      <MicButton onAudio={onAudio} busy={busy} label={`Speak ${NAMES[src]}`} />

      {error && <p className="error-msg">{error}</p>}

      {/* Translation History */}
      {log.length > 0 && (
        <>
          <div className="section-header" style={{ marginTop: 8 }}>
            <div>
              <div className="section-title">Translation History</div>
              <div className="section-subtitle">{log.length} translation{log.length > 1 ? "s" : ""}</div>
            </div>
          </div>

          <ul className="translation-log">
            {log.map((m, i) => (
              <li key={i} className="translation-item">
                <div className="translation-original">{m.text}</div>
                <div className="translation-result">{m.translation}</div>
                <button
                  className="translation-replay"
                  onClick={() => new Audio(m.audio_url).play()}
                >
                  ▶ Replay
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}
