// src/application/ports/solver.service.ts

import type {
  DeleteParams,
  FetchParams,
  InsertParams,
  SolveMultipleParams,
  SolveParams,
} from "@/entities/models/solver.model";
import type { ScheduleSolutionRaw } from "@/entities/models/schedule.model";

// --- Result Types (technology-agnostic) ---

export interface SolverHealthResult {
  healthy: boolean;
  message: string;
  details?: string;
}

export interface SolverOperationResult {
  success: boolean;
  duration?: number;
  error?: string;
  consoleOutput?: string;
}

export interface SolveOperationResult extends SolverOperationResult {
  solution?: ScheduleSolutionRaw;
  status: "FEASIBLE" | "INFEASIBLE" | "UNKNOWN";
}

export interface SolveMultipleOperationResult extends SolverOperationResult {
  solutions: ScheduleSolutionRaw[];
  feasibleCount: number;
  /** The actual weight-preset indices that produced a feasible/optimal solution, in the same order as `solutions`. */
  feasibleWeightIds: number[];
}

export interface SolverProgress {
  isSolving: boolean;
  phase: string;
  weightId?: number;
  totalWeights?: number;
  timeoutForPhase3?: number;
}

// --- Port Interface ---

export interface ISolverService {
  /**
   * Prüft ob der Solver erreichbar und konfiguriert ist.
   */
  checkHealth(): Promise<SolverHealthResult>;

  /**
   * Holt aktuelle Daten aus TimeOffice und bereitet sie für den Solver vor.
   */
  fetchData(params: FetchParams): Promise<SolverOperationResult>;

  /**
   * Berechnet einen einzelnen Dienstplan.
   */
  solve(params: SolveParams): Promise<SolveOperationResult>;

  /**
   * Berechnet drei Dienstpläne mit verschiedenen Gewichtungen.
   */
  solveMultiple(params: SolveMultipleParams): Promise<SolveMultipleOperationResult>;

  /**
   * Schreibt eine Lösung zurück in TimeOffice.
   */
  insertSolution(params: InsertParams, solution?: ScheduleSolutionRaw): Promise<SolverOperationResult>;

  /**
   * Setzt die Daten in TimeOffice zurück.
   */
  deleteData(params: DeleteParams, solution?: ScheduleSolutionRaw): Promise<SolverOperationResult>;

  /**
   * Gibt den aktuellen Lösungsfortschritt zurück, falls die
   * Implementierung Progress-Tracking unterstützt.
   * Gibt null zurück wenn nicht unterstützt (z.B. CLI).
   */
  getProgress(): Promise<SolverProgress | null>;
}
