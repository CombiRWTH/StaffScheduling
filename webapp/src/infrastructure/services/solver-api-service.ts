import { request as httpRequest } from 'http';
import { request as httpsRequest } from 'https';
import { createApiLogger } from '@/lib/logging/logger';
import { getSolverApiConfig } from '@/lib/config/app-config';
import type {
    DeleteParams,
    FetchParams,
    InsertParams,
    SolveMultipleParams,
    SolveParams,
} from '@/entities/models/solver.model';
import type {
    ISolverService,
    SolverHealthResult,
    SolverOperationResult,
    SolveOperationResult,
    SolveMultipleOperationResult, SolverProgress,
} from '@/application/ports/solver.service';
import type { ScheduleSolutionRaw } from '@/entities/models/schedule.model';

const logger = createApiLogger('solver-api-service');

// ---------------------------------------------------------------------------
// API response types mirroring src/api/main.py.
// ---------------------------------------------------------------------------

interface ApiStatusResponse {
    is_solving: boolean;
    phase: string;
    timeout_set_for_phase_3: number;
    weight_id?: number;
    total_weights?: number;
}

interface ApiOperationResponse {
    success: boolean;
    log?: string;
    stdout?: string;
    console_output?: string;
}

interface ApiSolveResponse extends ApiOperationResponse {
    status: string;
    solution_data: ScheduleSolutionRaw | null;
}

interface ApiSolveMultipleResult {
    weight_id: number;
    status: string;
    solution_data: ScheduleSolutionRaw | null;
}

interface ApiSolveMultipleResponse extends ApiOperationResponse {
    results: ApiSolveMultipleResult[];
}

// ---------------------------------------------------------------------------
// HTTP helpers.
// ---------------------------------------------------------------------------

async function apiPost<TBody, TResponse>(
    baseUrl: string,
    path: string,
    body: TBody,
    timeoutMs?: number
): Promise<TResponse> {
    return new Promise<TResponse>((resolve, reject) => {
        const url = new URL(`${baseUrl}${path}`);
        const payload = JSON.stringify(body);
        const request = url.protocol === 'https:' ? httpsRequest : httpRequest;

        const req = request(
            url,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(payload),
                },
            },
            (response) => {
                const chunks: Buffer[] = [];

                response.on('data', (chunk: Buffer) => chunks.push(chunk));
                response.on('end', () => {
                    if (timerId !== undefined) clearTimeout(timerId);

                    const responseText = Buffer.concat(chunks).toString('utf-8');
                    const statusCode = response.statusCode ?? 0;

                    if (statusCode < 200 || statusCode >= 300) {
                        reject(new Error(`HTTP ${statusCode}: ${responseText || response.statusMessage || 'Unknown error'}`));
                        return;
                    }

                    try {
                        resolve(JSON.parse(responseText) as TResponse);
                    } catch (error) {
                        reject(error);
                    }
                });
            }
        );

        const timerId = timeoutMs
            ? setTimeout(() => {
                req.destroy(new Error(`Request timed out after ${timeoutMs}ms`));
            }, timeoutMs)
            : undefined;

        req.on('error', (error) => {
            if (timerId !== undefined) clearTimeout(timerId);
            reject(error);
        });

        req.write(payload);
        req.end();
    });
}

async function apiGet<TResponse>(baseUrl: string, path: string): Promise<TResponse> {
    const response = await fetch(`${baseUrl}${path}`);

    if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    return response.json() as Promise<TResponse>;
}

// The API expects ISO dates (YYYY-MM-DD), unlike the CLI.
function toIsoDate(date: string | Date): string {
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toISOString().split('T')[0];
}

function formatUnitForLog(unit: number | number[]): string {
    return Array.isArray(unit) ? unit.join(',') : String(unit);
}

// ---------------------------------------------------------------------------
// ISolverService implementation.
// ---------------------------------------------------------------------------

export class SolverApiService implements ISolverService {
    private readonly baseUrl: string;

    constructor() {
        const config = getSolverApiConfig();
        this.baseUrl = config.baseUrl; // For example: 'http://127.0.0.1:8000'
    }

    async checkHealth(): Promise<SolverHealthResult> {
        const startTime = Date.now();
        try {
            const status = await apiGet<ApiStatusResponse>(this.baseUrl, '/status');
            const duration = Date.now() - startTime;

            logger.info('Solver API health check passed', { duration, phase: status.phase });

            return {
                healthy: true,
                message: status.is_solving
                    ? `Solver is currently solving (phase: ${status.phase})`
                    : 'Solver API is healthy and idle',
                // if phase is idle, weight_id and total_weights might be undefined, so we only show them if phase is not idle
                details: status.phase === 'idle'
                    ? ''
                    : `Phase: ${status.phase}${status.weight_id !== undefined ? `, Weight ID: ${status.weight_id}` : ''}, Total Weights: ${status.total_weights ?? 'N/A'}, Timeout for Phase 3: ${status.timeout_set_for_phase_3}s`,
            };
        } catch (error) {
            const duration = Date.now() - startTime;
            const message = error instanceof Error ? error.message : String(error);

            logger.error('Solver API health check failed', { duration, error: message });

            return {
                healthy: false,
                message: 'Solver API is not reachable',
                details: message,
            };
        }
    }

    async fetchData(params: FetchParams): Promise<SolverOperationResult> {
        const startTime = Date.now();
        logger.info('Fetching data via API', { unit: formatUnitForLog(params.unit), start: params.start, end: params.end });

        try {
            const result = await apiPost<object, ApiOperationResponse>(
                this.baseUrl,
                '/fetch',
                {
                    planning_unit: params.unit,
                    from_date: toIsoDate(params.start),
                    till_date: toIsoDate(params.end),
                }
            );

            const duration = Date.now() - startTime;
            logger.info('Fetch completed', { success: result.success, duration });

            return {
                success: result.success,
                duration,
                error: result.success ? undefined : result.log,
                consoleOutput: result.console_output
            };
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            logger.error('Fetch failed', { error: message });
            return { success: false, duration: Date.now() - startTime, error: message };
        }
    }

    async solve(params: SolveParams): Promise<SolveOperationResult> {
        const startTime = Date.now();
        logger.info('Solving via API', { unit: formatUnitForLog(params.unit), start: params.start, end: params.end, timeout: params.timeout });

        // Stretch the HTTP timeout beyond the solver timeout to avoid premature aborts.
        const solverTimeoutSec = params.timeout ?? 300;
        const httpTimeoutMs = (solverTimeoutSec + 30) * 2 * 1000;
        const [yearStr, monthStr] =  toIsoDate(params.start).split("-");

        const year = Number(yearStr);
        const month = Number(monthStr);
        try {
            const result = await apiPost<object, ApiSolveResponse>(
                this.baseUrl,
                '/solve/',
                {
                    planning_unit_ids: params.unit,
                    year: year,
                    month: month
                   // start_date: toIsoDate(params.start),
                   // end_date: toIsoDate(params.end),
                   // timeout: solverTimeoutSec,
                },
                httpTimeoutMs
            );

            const duration = Date.now() - startTime;
            const status = result.status as SolveOperationResult['status'];

            logger.info('Solve completed', { success: result.success, status, duration });

            if (!result.success || !result.solution_data) {
                return {
                    success: false,
                    status: (result.status as SolveOperationResult['status']) ?? 'UNKNOWN',
                    duration,
                    error: result.log ?? 'No solution produced',
                    consoleOutput: result.console_output,
                };
            }

            return {
                success: true,
                status,
                solution: result.solution_data,
                duration,
                consoleOutput: result.console_output,
            };
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            logger.error('Solve failed', { error: message });
            return { success: false, status: 'UNKNOWN', duration: Date.now() - startTime, error: message };
        }
    }

    async solveMultiple(params: SolveMultipleParams): Promise<SolveMultipleOperationResult> {
        const startTime = Date.now();
        logger.info('Solving multiple via API', { unit: formatUnitForLog(params.unit), timeout: params.timeout });

        // solve-multiple runs three solver passes, so give it a larger timeout buffer.
        const solverTimeoutSec = params.timeout ?? 300;
        const httpTimeoutMs = (solverTimeoutSec * 3 + 60) * 2 * 1000;

        try {
            const result = await apiPost<object, ApiSolveMultipleResponse>(
                this.baseUrl,
                '/solve-multiple',
                {
                    unit: params.unit,
                    start_date: toIsoDate(params.start),
                    end_date: toIsoDate(params.end),
                    timeout: solverTimeoutSec,
                },
                httpTimeoutMs
            );
            const duration = Date.now() - startTime;

            const feasibleResults = result.results.filter(
                (r) => r.status === 'FEASIBLE' || r.status === 'OPTIMAL'
            );
            const solutions = feasibleResults
                .map((r) => r.solution_data)
                .filter((s): s is ScheduleSolutionRaw => s !== null);
            const feasibleWeightIds = feasibleResults.map((r) => r.weight_id);

            logger.info('Solve-multiple completed', {
                success: result.success,
                feasibleCount: solutions.length,
                feasibleWeightIds,
                totalRuns: result.results.length,
                duration,
            });

            return {
                success: solutions.length > 0,
                solutions,
                feasibleCount: solutions.length,
                feasibleWeightIds,
                duration,
                error: solutions.length === 0 ? 'No feasible solutions produced' : undefined,
                consoleOutput: result.console_output,
            };
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            logger.error('Solve-multiple failed', { error: message });
            return { success: false, solutions: [], feasibleCount: 0, feasibleWeightIds: [], duration: Date.now() - startTime, error: message };
        }
    }

    async insertSolution(params: InsertParams, solution?: ScheduleSolutionRaw): Promise<SolverOperationResult> {
        const startTime = Date.now();
        logger.info('Inserting solution via API', { unit: formatUnitForLog(params.unit) });

        try {
            const result = await apiPost<object, ApiOperationResponse>(
                this.baseUrl,
                '/insert',
                {
                    planning_unit: params.unit,
                    from_date: toIsoDate(params.start),
                    till_date: toIsoDate(params.end),
                    solution_data: solution ?? null,
                }
            );

            const duration = Date.now() - startTime;
            logger.info('Insert completed', { success: result.success, duration });

            return {
                success: result.success,
                duration,
                error: result.success ? undefined : result.log,
                consoleOutput: result.console_output,
            };
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            logger.error('Insert failed', { error: message });
            return { success: false, duration: Date.now() - startTime, error: message };
        }
    }

    async deleteData(params: DeleteParams, solution?: ScheduleSolutionRaw): Promise<SolverOperationResult> {
        const startTime = Date.now();
        logger.info('Deleting data via API', { unit: formatUnitForLog(params.unit) });

        try {
            const result = await apiPost<object, ApiOperationResponse>(
                this.baseUrl,
                '/delete',
                {
                    planning_unit: params.unit,
                    from_date: toIsoDate(params.start),
                    till_date: toIsoDate(params.end),
                    solution_data: solution ?? null,
                }
            );

            const duration = Date.now() - startTime;
            logger.info('Delete completed', { success: result.success, duration });

            return {
                success: result.success,
                duration,
                error: result.success ? undefined : result.log,
                consoleOutput: result.console_output,
            };
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            logger.error('Delete failed', { error: message });
            return { success: false, duration: Date.now() - startTime, error: message };
        }
    }

    async getProgress(): Promise<SolverProgress | null> {
        try {
            const status = await apiGet<ApiStatusResponse>(this.baseUrl, '/status');
            return {
                isSolving: status.is_solving,
                phase: status.phase,
                weightId: status.weight_id,
                totalWeights: status.total_weights,
                timeoutForPhase3: status.timeout_set_for_phase_3,
            };
        } catch {
            return null;
        }
    }
}
