import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");

  return {
    plugins: [react()],
    server: {
      port: 3001,
      host: "0.0.0.0",
      proxy: {
        "/books": {
          target:
            process.env.VITE_API_PROXY_TARGET ||
            env.VITE_API_PROXY_TARGET ||
            "http://localhost:8001",
          changeOrigin: true,
        },
      },
    },
  };
});