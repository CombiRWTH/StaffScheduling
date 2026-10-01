/**
 * Minimal structured logger for server-side execution.
 * Wraps console methods and guarantees JSON-serializable metadata payloads.
 */
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

type LogMeta = Record<string, unknown> | undefined;

const levelToConsole: Record<LogLevel, (...args: unknown[]) => void> = {
    debug: console.debug,
    info: console.info,
    warn: console.warn,
    error: console.error,
};

function serializeMeta(meta: LogMeta) {
    if (!meta) {
        return undefined;
    }

    const safeEntries = Object.entries(meta).map(([key, value]) => [key, serializeValue(value)]);
    return Object.fromEntries(safeEntries);
}

function serializeValue(value: unknown): unknown {
    if (value instanceof Error) {
        return {
            name: value.name,
            message: value.message,
            stack: value.stack,
        };
    }

    if (typeof value === 'bigint') {
        return value.toString();
    }

    if (value === undefined) {
        return null;
    }

    if (Array.isArray(value)) {
        return value.map(serializeValue);
    }

    if (value && typeof value === 'object') {
        try {
            return JSON.parse(JSON.stringify(value));
        } catch (error) {
            return {description: 'Unserializable object', error: (error as Error)?.message};
        }
    }

    return value;
}

function log(level: LogLevel, message: string, meta?: LogMeta) {
    const timestamp = new Date().toISOString();
    const serializedMeta = serializeMeta(meta);
    const metaString = serializedMeta ? ` ${JSON.stringify(serializedMeta)}` : '';
    const output = `[${timestamp}] [${level.toUpperCase()}] ${message}${metaString}`;
    levelToConsole[level](output);
}

export const logger = {
    debug(message: string, meta?: LogMeta) {
        log('debug', message, meta);
    },
    info(message: string, meta?: LogMeta) {
        log('info', message, meta);
    },
    warn(message: string, meta?: LogMeta) {
        log('warn', message, meta);
    },
    error(message: string, meta?: LogMeta) {
        log('error', message, meta);
    },
};

export function createApiLogger(route: string) {
    const baseMeta = {route};
    return {
        debug(message: string, meta?: LogMeta) {
            logger.debug(message, {...baseMeta, ...meta});
        },
        info(message: string, meta?: LogMeta) {
            logger.info(message, {...baseMeta, ...meta});
        },
        warn(message: string, meta?: LogMeta) {
            logger.warn(message, {...baseMeta, ...meta});
        },
        error(message: string, meta?: LogMeta) {
            logger.error(message, {...baseMeta, ...meta});
        },
    };
}
