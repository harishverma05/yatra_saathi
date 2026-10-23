import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy API + audio to FastAPI so the frontend never deals with CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/audio": "http://localhost:8000",
    },
  },
});
