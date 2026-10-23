async function handle(res) {
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      msg = (await res.json()).detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

const withAudio = (url, blob, fields) => {
  const form = new FormData();
  const isMp4 = (blob.type || "").toLowerCase().includes("mp4");
  const cleanMime = isMp4 ? "audio/mp4" : "audio/webm";
  const cleanFilename = isMp4 ? "audio.mp4" : "audio.webm";
  const normalizedBlob = (blob.type && blob.type.includes(";"))
    ? new Blob([blob], { type: cleanMime })
    : blob;
  form.append("audio", normalizedBlob, cleanFilename);
  Object.entries(fields).forEach(([k, v]) => form.append(k, v));
  return fetch(url, { method: "POST", body: form }).then(handle);
};

export const getLandmarks = () => fetch("/api/landmarks").then(handle);
export const narrate = (id, lang) => fetch(`/api/narrate/${id}?lang=${lang}`).then(handle);
export const ask = (blob, landmark, lang) => withAudio("/api/ask", blob, { landmark, lang });
export const interpret = (blob, src, tgt) => withAudio("/api/interpret", blob, { src, tgt });
export const getStats = () => fetch("/api/stats").then(handle);
