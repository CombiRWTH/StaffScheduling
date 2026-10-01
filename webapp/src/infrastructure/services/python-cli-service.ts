// src/infrastructure/services/python-cli-service.ts

import {spawnSync, SpawnSyncReturns} from 'child_process';
import {existsSync, promises as fsPromises, readdirSync, readFileSync, statSync} from 'fs';
import path from 'path';
import {getPythonConfig, validatePythonConfig} from '@/lib/config/app-config';
import {createApiLogger} from '@/lib/logging/logger';
import type {
    DeleteParams,
    FetchParams,
    InsertParams,
    PythonCommandResult,
    SolveMultipleParams,
    SolveParams,
} from '@/entities/models/solver.model';
import type {
    ISolverService,
    SolveMultipleOperationResult,
    SolveOperationResult,
    SolverHealthResult,
    SolverOperationResult,
    SolverProgress,
} from '@/application/ports/solver.service';
import type {ScheduleSolutionRaw} from '@/entities/models/schedule.model';

const logger = createApiLogger('python-cli-service');

// --- Private Helpers ---

function formatDateForPython(date: string | Date): string {
    const d = typeof date === 'string' ? new Date(date) : date;
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}.${month}.${year}`;
}

function formatDateForFilename(date: string | Date): string {
    const d = typeof date === 'string' ? new Date(date) : date;
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${year}-${month}-${day}`;
}

function executePythonCommand(
    command: string,
    args: string[],
    timeoutMs?: number,
    useEnvFile: boolean = false
): PythonCommandResult {
    const startTime = Date.now();
    const pythonConfig = getPythonConfig();

    logger.info('Executing Python command', {
        command,
        args,
        pythonExecutable: pythonConfig.pythonExecutable,
        projectPath: pythonConfig.path,
        useEnvFile,
    });

    const commandArgs = useEnvFile
        ? ['run', '--env-file', '.env', 'python', '-m', 'app.cli', command, ...args]
        : ['run', 'python', '-m', 'app.cli', command, ...args];

    logger.debug('Spawning process', {
        command: pythonConfig.pythonExecutable,
        fullArgs: commandArgs,
    });

    try {
        const result: SpawnSyncReturns<string> = spawnSync(
            pythonConfig.pythonExecutable,
            commandArgs,
            {
                cwd: pythonConfig.path,
                encoding: 'utf-8',
                timeout: timeoutMs,
                maxBuffer: 10 * 1024 * 1024,
                shell: process.platform === 'win32',
                env: {
                    ...process.env,
                    PYTHONUNBUFFERED: '1',
                },
            }
        );

        const duration = Date.now() - startTime;
        const exitCode = result.status ?? -1;
        const consoleOutput = (result.stdout || '') + (result.stderr || '');

        if (result.error) {
            logger.error('Python command execution error', {command, error: result.error.message, duration});
            return {success: false, consoleOutput: result.error.message, exitCode: -1, duration};
        }

        let success = exitCode === 0;

        if (command === 'solve' || command === 'solve-multiple') {
            success = consoleOutput.includes('- status         : FEASIBLE');
            if (success) {
                logger.info(`${command} completed with FEASIBLE status`, {exitCode});
            } else {
                logger.warn(`${command} did not produce FEASIBLE status`, {exitCode});
            }
        }

        if (!success) {
            logger.warn('Python command failed', {command, exitCode, duration});
        } else {
            logger.info('Python command completed successfully', {command, duration});
        }

        return {success, consoleOutput, exitCode, duration};
    } catch (error) {
        const duration = Date.now() - startTime;
        logger.error('Unexpected error executing Python command', {
            command,
            error: error instanceof Error ? error.message : String(error),
            duration,
        });
        return {
            success: false,
            consoleOutput: error instanceof Error ? error.message : String(error),
            exitCode: -1,
            duration,
        };
    }
}

// --- Private File Helpers (CLI-internal, not on interface) ---

function getSolutionDir(): string {
    const pythonConfig = getPythonConfig();
    return path.join(pythonConfig.path, 'found_solutions');
}

function getProcessedSolutionsDir(): string {
    const pythonConfig = getPythonConfig();
    return path.join(pythonConfig.path, 'processed_solutions');
}

function getProcessedSolutionDir(): string {
    const pythonConfig = getPythonConfig();
    return path.join(pythonConfig.path, 'processed_solutions');
}

function readJsonFile(filePath: string): ScheduleSolutionRaw {
    const content = readFileSync(filePath, 'utf-8');
    return JSON.parse(content) as ScheduleSolutionRaw;
}

/**
 * Finds solution files created/modified after the given timestamp.
 * Used to detect which files a solve run produced.
 */
function findNewSolutionFiles(sinceTimestamp: number): string[] {
    const dir = getProcessedSolutionsDir();
    if (!existsSync(dir)) return [];

    return readdirSync(dir)
        .filter((f) => f.endsWith('.json'))
        .map((f) => path.join(dir, f))
        .filter((f) => statSync(f).mtimeMs >= sinceTimestamp)
        .sort((a, b) => statSync(a).mtimeMs - statSync(b).mtimeMs);
}

// --- ISolverService Implementation ---

export class PythonCliService implements ISolverService {

    async getProgress(): Promise<SolverProgress | null> {
        return null;
    }

    async checkHealth(): Promise<SolverHealthResult> {
        try {
            const configValidation = validatePythonConfig();
            const pythonConfig = getPythonConfig();

            if (!configValidation.isEnabled) {
                return {healthy: false, message: 'Python solver integration is not enabled in configuration'};
            }

            if (!configValidation.isValid) {
                return {
                    healthy: false,
                    message: 'Invalid Python configuration',
                    details: configValidation.errors.join(', ')
                };
            }

            const result = spawnSync(pythonConfig.pythonExecutable, ['--version'], {
                cwd: pythonConfig.path,
                encoding: 'utf-8',
                timeout: 5000,
                shell: process.platform === 'win32',
            });

            if (result.error || result.status !== 0) {
                return {
                    healthy: false,
                    message: 'Python executable test failed',
                    details: result.error?.message ?? result.stderr ?? 'Unknown error',
                };
            }

            return {
                healthy: true,
                message: 'Python CLI solver is healthy',
                details: (result.stdout || result.stderr || '').trim(),
            };
        } catch (error) {
            return {
                healthy: false,
                message: 'Unexpected error checking Python CLI health',
                details: error instanceof Error ? error.message : String(error),
            };
        }
    }

    async fetchData(params: FetchParams): Promise<SolverOperationResult> {
        const args = [
            String(params.unit),
            formatDateForPython(params.start),
            formatDateForPython(params.end),
        ];
        const result = executePythonCommand('fetch', args, undefined, true);
        return {
            success: result.success,
            duration: result.duration,
            error: result.success ? undefined : result.consoleOutput,
            consoleOutput: result.consoleOutput,
        };
    }

    async solve(params: SolveParams): Promise<SolveOperationResult> {
        const args = [
            String(params.unit),
            formatDateForPython(params.start),
            formatDateForPython(params.end),
        ];

        if (params.timeout) {
            args.push('--timeout', String(params.timeout));
        }

        const timeoutMs = params.timeout ? (params.timeout + 10) * 2 * 1000 : undefined;
        const beforeRun = Date.now();
        const result = executePythonCommand('solve', args, timeoutMs);

        if (!result.success)  {
            return {
                success: false,
                status: 'INFEASIBLE',
                duration: result.duration,
                error: result.consoleOutput,
                consoleOutput: result.consoleOutput,
            };
        }

        const newFiles = findNewSolutionFiles(beforeRun);
        if (newFiles.length === 0) {
            logger.warn('solve succeeded but no new solution file found');
            return {
                success: false,
                status: 'UNKNOWN',
                duration: result.duration,
                error: 'No solution file produced by solver',
                consoleOutput: result.consoleOutput,
            };
        }

        const solution = readJsonFile(newFiles[0]);
        return {
            success: true,
            status: 'FEASIBLE',
            solution,
            duration: result.duration,
            consoleOutput: result.consoleOutput,
        };
    }

    async solveMultiple(params: SolveMultipleParams): Promise<SolveMultipleOperationResult> {
        const args = [
            String(params.unit),
            formatDateForPython(params.start),
            formatDateForPython(params.end),
        ];

        if (params.timeout) {
            args.push('--timeout', String(params.timeout));
        }

        const timeoutMs = params.timeout ? (params.timeout * 3 + 30) * 2 * 1000 : undefined;
        const beforeRun = Date.now();
        const result = executePythonCommand('solve-multiple', args, timeoutMs);

        if (!result.success) {
            return {
                success: false,
                solutions: [],
                feasibleCount: 0,
                feasibleWeightIds: [],
                duration: result.duration,
                error: result.consoleOutput,
                consoleOutput: result.consoleOutput,
            };
        }

        const newFiles = findNewSolutionFiles(beforeRun);

        // Extract weight ID from filenames like "solution_77_..._w2.json" → 2
        // Fall back to sequential index if the pattern is not found (e.g. legacy files).
        const parseWeightId = (filePath: string, fallback: number): number => {
            const match = path.basename(filePath).match(/_w(\d+)\.json$/);
            return match ? parseInt(match[1], 10) : fallback;
        };

        const solutions = newFiles.map((f) => readJsonFile(f));
        const feasibleWeightIds = newFiles.map((f, i) => parseWeightId(f, i));

        return {
            success: solutions.length > 0,
            solutions,
            feasibleCount: solutions.length,
            feasibleWeightIds,
            duration: result.duration,
            consoleOutput: result.consoleOutput,
        };
    }

    async insertSolution(params: InsertParams, _solution?: ScheduleSolutionRaw): Promise<SolverOperationResult> {
        // If a solution is provided, we write it to the expected location before running the insert command
        // Example: solution_77_2024-01-01-2024-01-31.json"
        if (_solution) {
            const filename = `solution_${params.unit}_${formatDateForFilename(params.start)}-${formatDateForFilename(params.end)}.json`;
            await this.writeSolutionFile(filename, _solution);
        }

        const args = [String(params.unit), formatDateForPython(params.start), formatDateForPython(params.end)];
        const result = executePythonCommand('insert', args, undefined, true);
        return {
            success: result.success,
            duration: result.duration,
            error: result.success ? undefined : result.consoleOutput,
            consoleOutput: result.consoleOutput,
        };
    }

    async deleteData(params: DeleteParams, _solution?: ScheduleSolutionRaw): Promise<SolverOperationResult> {
        // If a solution is provided, we write it to the expected location before running the delete command
        // Example: solution_77_2024-01-01-2024-01-31.json"
        if (_solution) {
            const filename = `solution_${params.unit}_${formatDateForFilename(params.start)}-${formatDateForFilename(params.end)}.json`;
            await this.writeSolutionFile(filename, _solution);
        }

        const args = [
            String(params.unit),
            formatDateForPython(params.start),
            formatDateForPython(params.end),
        ];
        const result = executePythonCommand('delete', args, undefined, true);
        return {
            success: result.success,
            duration: result.duration,
            error: result.success ? undefined : result.consoleOutput,
            consoleOutput: result.consoleOutput,
        };
    }

    // --- Private helpers still available internally if needed by use cases ---

    async writeSolutionFile(filename: string, content: ScheduleSolutionRaw): Promise<void> {
        const targetDir = getSolutionDir();
        const targetPath = path.join(targetDir, filename);
        await fsPromises.mkdir(targetDir, {recursive: true});
        await fsPromises.writeFile(targetPath, JSON.stringify(content, null, 2), 'utf8');
    }

    readSolutionFile(filename: string): ScheduleSolutionRaw {
        return readJsonFile(path.join(getProcessedSolutionsDir(), filename));
    }

    readProcessedSolutionFile(filename: string): ScheduleSolutionRaw {
        return readJsonFile(path.join(getProcessedSolutionDir(), filename));
    }
}
