import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  agentRules: false,
  // An imported input.json/result.json pair of a full month passes through a server action.
  experimental: { serverActions: { bodySizeLimit: "5mb" } },
};

export default nextConfig;
