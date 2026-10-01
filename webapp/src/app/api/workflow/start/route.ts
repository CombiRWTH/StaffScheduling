import {NextRequest, NextResponse} from 'next/server';
import {setWorkflowSession} from '@/infrastructure/services/workflow-session.service';

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const caseId = searchParams.get('caseId') ?? '';
    const start = searchParams.get('start') ?? '';
    const end = searchParams.get('end') ?? '';

    await setWorkflowSession(caseId, start, end);

    return NextResponse.redirect(new URL('/workflow', request.url));
}
