import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a self-contained server bundle (node_modules pruned to only what's
  // needed at runtime) — used when this app is packaged into the combined
  // single-container deployment alongside the FastAPI backend. Has no effect
  // on `npm run dev`.
  output: "standalone",
};

export default nextConfig;
