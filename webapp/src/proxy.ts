import {NextRequest, NextResponse} from 'next/server';

const PROTECTED_PREFIXES = [
    '/employees',
    '/solver',
    '/wishes-and-blocked',
    '/schedule',
    '/weights',
    '/minimal-staff',
];

export function proxy(request: NextRequest) {
    // Ignore the request unless workflow mode is enabled.
    const workflowMode = request.cookies.get('workflow_mode')?.value;
    if (workflowMode !== 'true') {
        return NextResponse.next();
    }

    const { pathname } = request.nextUrl;

    // Only enforce workflow routing on protected pages.
    const isProtected = PROTECTED_PREFIXES.some((prefix) => pathname.startsWith(prefix));
    if (!isProtected) {
        return NextResponse.next();
    }

    // Read the workflow context from cookies.
    const cookieCaseId = request.cookies.get('workflow_case')?.value;
    const cookieStart = request.cookies.get('workflow_start')?.value;

    // Abort when workflow mode is active but required cookie state is missing.
    // This prevents redirects based on incomplete or corrupt workflow context.
    if (!cookieCaseId || !cookieStart) {
        return NextResponse.next();
    }

    // Derive MM_YYYY from DD.MM.YYYY — pure JS, Edge-compatible
    const parts = cookieStart.split('.');
    const cookieMonthYear = parts.length === 3
        ? `${parts[1].padStart(2, '0')}_${parts[2]}`
        : '';

    if (!cookieMonthYear) {
        return NextResponse.next();
    }

    // Redirect to the locked workflow case if the URL does not match the cookie state.
    const url = request.nextUrl.clone();
    const urlCaseId = url.searchParams.get('caseId');
    const urlMonthYear = url.searchParams.get('monthYear');

    if (urlCaseId !== cookieCaseId || urlMonthYear !== cookieMonthYear) {
        url.searchParams.set('caseId', cookieCaseId);
        url.searchParams.set('monthYear', cookieMonthYear);
        return NextResponse.redirect(url);
    }

    return NextResponse.next();
}

export const config = {
    matcher: ['/((?!api|_next/static|_next/image|favicon\\.ico).*)'],
};
