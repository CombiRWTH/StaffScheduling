import { join, resolve } from "node:path";

export function getCasesDirectory(): string {
  return resolve(process.env.CASES_DIR ?? "../data/cases");
}

export interface SolverApiConfig {
  baseUrl: string;
}

export function getSolverApiConfig(): SolverApiConfig {
  const url = new URL(process.env.SOLVER_API_URL ?? "http://127.0.0.1:8000");
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
    throw new Error("SOLVER_API_URL must be an HTTP(S) URL without credentials, query or fragment.");
  }
  return { baseUrl: url.toString().replace(/\/$/, "") };
}

export const CASES_DIR = getCasesDirectory();

export function getCasePath(caseId: number, monthYear: string): string {
  return join(CASES_DIR, caseId.toString(), monthYear);
}
