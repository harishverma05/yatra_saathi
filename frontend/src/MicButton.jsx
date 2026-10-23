import useRecorder from "./hooks/useRecorder.js";

// Premium tap-to-talk button. Calls onAudio(blob) when recording stops.
export default function MicButton({ onAudio, busy, label = "Tap to speak" }) {
  const { recording, start, stop } = useRecorder();

  const toggle = async () => {
    if (busy) return;
    try {
      if (recording) onAudio(await stop());
      else await start();
    } catch (e) {
      alert("Microphone unavailable: " + e.message + "\n(Phones need HTTPS or localhost.)");
    }
  };

  return (
    <div className="mic-section">
      <button
        className={`mic-btn ${recording ? "recording" : ""}`}
        onClick={toggle}
        disabled={busy}
      >
        {busy ? "…" : recording ? "■" : "🎙"}
        <span>{busy ? "Working" : recording ? "Stop" : ""}</span>
      </button>
      <span className="mic-label">
        {busy ? "Processing your audio…" : recording ? "Tap to stop recording" : label}
      </span>
    </div>
  );
}
