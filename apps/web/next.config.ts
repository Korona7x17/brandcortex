import type { NextConfig } from "next";

/**
 * The dashboard talks to the API over HTTP and holds no database connection of its own. That keeps
 * the one-way import direction from the spec intact across the language boundary: every rule about
 * what may be published lives in the API, and a UI cannot route around a check by writing directly.
 */
const config: NextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  },
};

export default config;
