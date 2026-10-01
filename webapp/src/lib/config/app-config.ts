import {join} from 'path';
import {existsSync, readFileSync} from 'fs';

/**
 * Solver mode type definition.
 * @type {'cli' | 'api'}
 * @description 'cli' for local Python CLI execution, 'api' for remote FastAPI server
 */
export type SolverMode = 'cli' | 'api';

/**
 * Application configuration structure.
 */
interface AppConfig {
    /**
     * Path to the cases directory.
     * Can be absolute or relative to the project root.
     * If relative, it will be resolved from process.cwd().
     *
     * @example "/absolute/path/to/cases"
     * @example "cases" (relative to webapp root)
     * @example "data/cases" (relative to project root)
     */
    casesDirectory: string;

    /**
     * StaffScheduling Python project configuration.
     */
    staffSchedulingProject: {
        /**
         * Whether to enable Python solver integration.
         */
        include: boolean;

        /**
         * Absolute path to the StaffScheduling Python project directory.
         * Should contain the main Python CLI entry point.
         */
        path: string;

        /**
         * Python executable command (e.g., 'uv', 'python', 'python3').
         * @default 'uv'
         */
        pythonExecutable: string;
    };

    /**
     * Solver mode: 'cli' for local Python CLI execution, 'api' for remote FastAPI server.
     * Start the API separately before using API mode.
     * @default 'cli'
     */
    solverMode: SolverMode;
}

/**
 * Loads the application configuration.
 * First tries to load config.json, falls back to config.template.json if not found.
 * @returns The application configuration
 * @throws Error if neither config file can be read or parsed
 */
function loadConfig(): AppConfig {
    const configPath = join(process.cwd(), 'config.json');
    const templatePath = join(process.cwd(), 'config.template.json');

    let pathToUse = configPath;

    // Check if config.json exists, otherwise use template
    if (!existsSync(configPath)) {
        pathToUse = templatePath;
    }

    try {
        const configContent = readFileSync(pathToUse, 'utf-8');
        return JSON.parse(configContent) as AppConfig;
    } catch (error) {
        throw new Error(
            `Failed to load config file (${pathToUse}): ${error instanceof Error ? error.message : String(error)}`
        );
    }
}

/**
 * Gets the absolute path to the cases directory.
 * Resolves relative paths from the project root (process.cwd()).
 *
 * @returns Absolute path to the cases directory
 *
 * @example
 * // With config.json (or config.template.json): { "casesDirectory": "cases" }
 * getCasesDirectory(); // Returns "/path/to/project/cases"
 *
 * @example
 * // With config.json (or config.template.json): { "casesDirectory": "/absolute/path/to/cases" }
 * getCasesDirectory(); // Returns "/absolute/path/to/cases"
 */
export function getCasesDirectory(): string {
    const config = loadConfig();
    const casesDir = config.casesDirectory;

    // Check if it's an absolute path
    // Windows: C:\ or C:/ or \\server\share (UNC paths)
    // Unix/Linux: /absolute/path
    const isWindowsAbsolute = /^[a-zA-Z]:[/\\]/.test(casesDir);
    const isUncPath = /^[/\\]{2}/.test(casesDir);
    const isUnixAbsolute = casesDir.startsWith('/') && process.platform !== 'win32';

    if (isWindowsAbsolute || isUncPath || isUnixAbsolute) {
        // It's an absolute path, return as-is
        return casesDir;
    }

    // It's a relative path, resolve from project root
    return join(process.cwd(), casesDir);
}

/**
 * Python configuration validation result.
 */
export interface PythonConfigValidation {
    /**
     * Whether the configuration is valid and ready to use.
     */
    isValid: boolean;

    /**
     * Whether Python solver integration is enabled.
     */
    isEnabled: boolean;

    /**
     * Validation error messages.
     */
    errors: string[];

    /**
     * Warning messages (non-critical issues).
     */
    warnings: string[];
}

/**
 * Gets the Python project configuration.
 * @returns Python project configuration from config file
 */
export function getPythonConfig() {
    const config = loadConfig();
    return config.staffSchedulingProject;
}

/**
 * Gets the complete application configuration.
 * @returns Application configuration from config file
 */
export function getAppConfig() {
    return loadConfig();
}

export interface SolverApiConfig {
    baseUrl: string;
}

export function getSolverApiConfig(): SolverApiConfig {
    const baseUrl = process.env.SOLVER_API_URL ?? 'http://127.0.0.1:8000';
    return { baseUrl };
}

/**
 * Validates the Python project configuration.
 * Checks if paths exist and are accessible.
 *
 * @returns Validation result with status and error/warning messages
 */
export function validatePythonConfig(): PythonConfigValidation {
    const result: PythonConfigValidation = {
        isValid: true,
        isEnabled: false,
        errors: [],
        warnings: []
    };

    try {
        const pythonConfig = getPythonConfig();
        result.isEnabled = pythonConfig.include;

        // If not enabled, no need to validate further
        if (!pythonConfig.include) {
            return result;
        }

        // Validate project path (must be set and not placeholder)
        if (!pythonConfig.path || pythonConfig.path === '-') {
            result.errors.push('Python project path is not configured');
            result.isValid = false;
            return result;
        }

        if (!existsSync(pythonConfig.path)) {
            result.errors.push(`Python project path does not exist: ${pythonConfig.path}`);
            result.isValid = false;
        }

        // Validate Python executable (path must be set)
        if (!pythonConfig.pythonExecutable) {
            result.errors.push('Python executable is not configured');
            result.isValid = false;
        }

        // Check if cases directory exists
        const casesDir = getCasesDirectory();
        if (!existsSync(casesDir)) {
            result.warnings.push(`Cases directory does not exist yet: ${casesDir}`);
        }

    } catch (error) {
        result.errors.push(
            `Failed to validate Python configuration: ${error instanceof Error ? error.message : String(error)}`
        );
        result.isValid = false;
    }

    return result;
}

/**
 * Root directory where all case data is stored.
 * Each case has its own subdirectory named by its case ID.
 * Within each case directory are month folders in MM_YYYY format.
 * The path is loaded from config.template.json.
 */
export const CASES_DIR = getCasesDirectory();

/**
 * Gets the absolute file system path for a specific case directory.
 *
 * @param caseId - The planning unit ID
 * @param monthYear - The month/year in MM_YYYY format
 * @returns The absolute path to the case directory
 *
 * @example
 * const path = getCasePath(77, "11_2024");
 * console.log(path); // '/path/to/project/cases/77/11_2024'
 */
export function getCasePath(caseId: number, monthYear: string): string {
    return join(CASES_DIR, caseId.toString(), monthYear);
}