import { NextResponse } from 'next/server';
import {getInjection} from "@/di/container";

/**
 * GET /api/solver/status
 *
 * Proxies GET /status from the Python solver API.
 * Must be a Route Handler (not a Server Action) so it can be called concurrently
 * from the browser while a Server Action (solve / solve-multiple) is in-flight.
 * Server Actions hold a per-session lock; Route Handlers do not.
 */
export async function GET() {
    try {
        const controller = getInjection('IGetSolverProgressController');
        const result = await controller();
        if ('error' in result) {
            return NextResponse.json(null); // Graceful degradation
        }
        return NextResponse.json(result.data); // SolverProgress | null
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return NextResponse.json({ error: message }, { status: 502 });
    }
}
