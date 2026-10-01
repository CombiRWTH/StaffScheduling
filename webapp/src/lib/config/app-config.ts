import { join, resolve } from "node:path";

export function getCasesDirectory(): string {
  return resolve(process.env.CASES_DIR ?? "../data/cases");
}

export interface SolverApiConfig {
  baseUrl: string;
}

export function getSolverApiConfig(): SolverApiConfig {
  return { baseUrl: process.env.SOLVER_API_URL ?? "http://127.0.0.1:8000" };
}

export const CASES_DIR = getCasesDirectory();

export function getCasePath(caseId: number, monthYear: string): string {
  return join(CASES_DIR, caseId.toString(), monthYear);
}
