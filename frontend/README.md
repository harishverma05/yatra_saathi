# 🎨 Yatra Saathi Frontend
### *Modern Responsive UI, Live Audio Visualizer & Cultural Portal*

The **Yatra Saathi Frontend** is a single-page web application developed with **React 18** and **Vite**. It provides an intuitive, tactile interface for exploring heritage landmarks, listening to studio-quality bilingual audio stories, and engaging in live bidirectional speech interpretation.

---

## 💎 Design Philosophy & Aesthetics

1. **Aesthetic Minimalism with Depth**: Crafted with tailored glassmorphic panels, translucent borders (`rgba(255, 255, 255, 0.08)`), subtle gradients, and an obsidian backdrop (`#0d0f12`) tailored for high-contrast legibility in varying lighting conditions.
2. **Dynamic Telemetry Integration**: Displays real-time API performance cards showcasing active landmarks, cumulative TTS calls, STT sessions, and ElevenLabs character costs directly in the dashboard.
3. **Micro-Interactions & Responsive Feedback**:
   - Pulse-animated microphone buttons (`MicButton.jsx`) indicating recording activity.
   - Smooth navigation transitions between the Dashboard, Cultural Guide, and Interpreter views.
   - Responsive off-canvas navigation drawer for handheld devices.

---

## 📂 Component Hierarchy & Organization

```
frontend/
├── public/
│   └── images/               # High-resolution heritage photography
│       ├── bara_imambara.jpg
│       ├── rumi_darwaza.jpg
│       └── tunday_kababi.jpg
├── src/
│   ├── hooks/
│   │   └── useRecorder.js    # Cross-browser MediaRecorder audio capture hook
│   ├── api.js                # Unified backend HTTP client with MIME sanitizer
│   ├── App.jsx               # Master layout shell, sidebar, and page routing
│   ├── Dashboard.jsx         # Metrics dashboard & landmark discovery cards
│   ├── Guide.jsx             # Landmark narration player & voice Q&A
│   ├── Interpreter.jsx       # Real-time bilingual speech-to-speech interpreter
│   ├── MicButton.jsx         # Tactile voice recording button with pulse glow
│   ├── styles.css            # Complete design system tokens & animation rules
│   └── main.jsx              # React DOM mounting entrypoint
├── index.html                # HTML5 entry with Google Fonts (Outfit / Inter)
├── package.json              # Dependencies and build scripts
├── vite.config.js            # Reverse-proxy configuration to FastAPI
└── README.md                 # This frontend manual
```

---

## 🎙️ Audio Recording Pipeline (`useRecorder.js` & `api.js`)

Different browsers produce different audio encodings:
- **Safari / iOS**: Encodes recordings as `audio/mp4` (`mp4a.40.2`).
- **Chromium / Android**: Encodes recordings as `audio/webm` (`opus`).

### How It Works:
1. `useRecorder` probes `MediaRecorder.isTypeSupported` to select the optimal container format:
   ```javascript
   const mimeType = MediaRecorder.isTypeSupported("audio/webm; codecs=opus")
     ? "audio/webm; codecs=opus"
     : MediaRecorder.isTypeSupported("audio/mp4")
     ? "audio/mp4"
     : "";
   ```
2. When recording stops, `api.js` automatically normalizes the `Blob` and strips any trailing codec parameters (e.g. `; codecs=...`) before multipart submission:
   ```javascript
   const isMp4 = (blob.type || "").toLowerCase().includes("mp4");
   const cleanMime = isMp4 ? "audio/mp4" : "audio/webm";
   const cleanFilename = isMp4 ? "audio.mp4" : "audio.webm";
   const normalizedBlob = (blob.type && blob.type.includes(";"))
     ? new Blob([blob], { type: cleanMime })
     : blob;
   form.append("audio", normalizedBlob, cleanFilename);
   ```

---

## ⚙️ Vite Reverse-Proxy Configuration

To eliminate CORS configuration issues during development, [`vite.config.js`](file:///Users/harishverma/Desktop/project/yatra-saathi/frontend/vite.config.js) proxies API and static audio calls directly to the FastAPI server:

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/audio": "http://localhost:8000",
    },
  },
});
```

---

## 🚀 Development & Build Scripts

```bash
# Install dependencies
npm install

# Run hot-reloading dev server (http://localhost:5173)
npm run dev

# Build optimized production bundle
npm run build

# Preview production build locally
npm run preview
```

---

## 📱 Mobile Device Testing

Mobile browsers require a secure origin (`https://` or `localhost`) to grant microphone access. To test on a physical smartphone:

```bash
# Using Cloudflare Tunnel
npx cloudflared tunnel --url http://localhost:5173

# Or using ngrok
npx ngrok http 5173
```
Load the generated HTTPS URL on your phone to test real-time voice recording, narration playback, and speech interpretation in the field!
