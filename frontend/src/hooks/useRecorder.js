import { useRef, useState } from "react";

// Tap to start, tap to stop. stop() resolves with the recorded audio Blob.
export default function useRecorder() {
  const [recording, setRecording] = useState(false);
  const recorder = useRef(null);
  const chunks = useRef([]);

  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const r = new MediaRecorder(stream);
    chunks.current = [];
    r.ondataavailable = (e) => e.data.size && chunks.current.push(e.data);
    recorder.current = r;
    r.start();
    setRecording(true);
  };

  const stop = () =>
    new Promise((resolve) => {
      const r = recorder.current;
      r.onstop = () => {
        r.stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
        resolve(new Blob(chunks.current, { type: r.mimeType || "audio/webm" }));
      };
      r.stop();
    });

  return { recording, start, stop };
}
