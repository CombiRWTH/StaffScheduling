'use client';

import {usePathname, useSearchParams} from 'next/navigation';
import Link from 'next/link';
import {useState} from 'react';
import {MonthSelector} from '@/components/month-selector';
import {Button} from '@/components/ui/button';
import {ScrollArea} from '@/components/ui/scroll-area';
import {
    Briefcase,
    Calendar,
    // CalendarCheck,
    Cog,
    // FileText,
    Heart,
    type LucideIcon,
    Menu,
    Scale,
    UserCog,
    X,
} from 'lucide-react';
import {cn} from '@/lib/utils';
// This wrapper is required because AppNavigation uses useSearchParams, a client hook.
// During SSR/prerendering it must be rendered inside a Suspense boundary.
import {Suspense} from 'react';

interface AppNavigationProps {
    isLocked: boolean;
    lockedCaseId?: number | null;
    lockedMonthYear?: string | null;
}

const mainLinks: Array<{ href: string; label: string; icon: LucideIcon }> = [
    {href: '/employees', label: 'Mitarbeiter', icon: Calendar},
    {href: '/schedule', label: 'Dienstplan', icon: Calendar},
    {href: '/solver', label: 'Solver', icon: Cog},
];

const groupedLinks: Array<{
    label: string;
    icon: LucideIcon;
    links: Array<{ href: string; label: string; icon: LucideIcon }>;
}> = [
    {
        label: 'Wünsche',
        icon: Heart,
        links: [
            // {href: '/global-wishes-and-blocked', label: 'Globale Wünsche', icon: Heart},
            {href: '/wishes-and-blocked', label: 'Wünsche diesen Monat', icon: Heart},
        ],
    },
    // {
    //     label: 'Availability',
    //     icon: CalendarCheck,
    //     links: [
    //         {href: '/global-availability', label: 'Global Availability', icon: CalendarCheck},
    //         {href: '/availability', label: 'Availability für den Monat', icon: CalendarCheck},
    //     ],
    // },
    {
        label: 'Konfiguration',
        icon: Cog,
        links: [
            {href: '/weights', label: 'Gewichtungen', icon: Scale},
            {href: '/minimal-staff', label: 'Mindestbesetzung', icon: UserCog},
        ],
    },
    // {
    //     label: 'Templates',
    //     icon: FileText,
    //     links: [
    //         {href: '/templates', label: 'Alle Templates', icon: FileText},
    //         {href: '/templates/weights', label: 'Gewichtungs-Templates', icon: Scale},
    //         {href: '/templates/global-wishes', label: 'Wünsche-Templates', icon: Heart},
    //         {href: '/templates/minimal-staff', label: 'Mindestbesetzung-Templates', icon: UserCog},
    //         {href: '/templates/availability', label: 'Availability-Templates', icon: CalendarCheck},
    //     ],
    // },
];

interface SidebarContentProps {
    caseSearch: string;
    isActive: (path: string) => boolean;
    onClose?: () => void;
    showCloseButton?: boolean;
}

function SidebarContent({
                            caseSearch,
                            isActive,
                            onClose,
                            showCloseButton = false,
                        }: SidebarContentProps) {
    return (
        <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
            <div className="flex h-16 shrink-0 items-center justify-between border-b border-sidebar-border px-4">
                <Link
                    href={`/${caseSearch}`}
                    className="flex min-w-0 items-center gap-2 hover:opacity-80 transition-opacity"
                    onClick={onClose}
                >
                    <Briefcase className="h-6 w-6 shrink-0"/>
                    <span className="truncate text-lg font-semibold">Schichtplan Manager</span>
                </Link>

                {showCloseButton && (
                    <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="md:hidden"
                        onClick={onClose}
                        aria-label="Navigation schließen"
                    >
                        <X className="h-5 w-5"/>
                    </Button>
                )}
            </div>

            <ScrollArea className="min-h-0 flex-1">
                <nav className="space-y-5 px-3 py-4">
                    <div className="space-y-1">
                        {mainLinks.map(({href, label, icon: Icon}) => (
                            <Button
                                key={href}
                                variant="ghost"
                                asChild
                                className={cn(
                                    'h-10 w-full justify-start gap-3 px-3',
                                    isActive(href) && 'bg-sidebar-accent text-sidebar-accent-foreground'
                                )}
                            >
                                <Link href={`${href}${caseSearch}`} onClick={onClose}>
                                    <Icon className="h-4 w-4"/>
                                    <span className="truncate">{label}</span>
                                </Link>
                            </Button>
                        ))}
                    </div>

                    {groupedLinks.map(({label, icon: GroupIcon, links}) => (
                        <section key={label} className="space-y-1">
                            <div className="flex items-center gap-2 px-3 pb-1 text-xs font-medium uppercase text-muted-foreground">
                                <GroupIcon className="h-3.5 w-3.5"/>
                                <span className="truncate">{label}</span>
                            </div>

                            {links.map(({href, label: linkLabel, icon: Icon}) => (
                                <Button
                                    key={href}
                                    variant="ghost"
                                    asChild
                                    className={cn(
                                        'h-10 w-full justify-start gap-3 px-3 text-sm',
                                        isActive(href) && 'bg-sidebar-accent text-sidebar-accent-foreground'
                                    )}
                                >
                                    <Link href={`${href}${caseSearch}`} onClick={onClose}>
                                        <Icon className="h-4 w-4"/>
                                        <span className="truncate">{linkLabel}</span>
                                    </Link>
                                </Button>
                            ))}
                        </section>
                    ))}
                </nav>
            </ScrollArea>
        </div>
    );
}

export function AppNavigation({isLocked, lockedCaseId, lockedMonthYear}: AppNavigationProps) {
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const [isMobileOpen, setIsMobileOpen] = useState(false);
    const caseId = searchParams.get('caseId');
    const caseIds = searchParams.get('caseIds');
    const monthYear = searchParams.get('monthYear');
    const caseSearch = caseId && monthYear
        ? `?caseId=${caseId}${caseIds ? `&caseIds=${caseIds}` : ''}&monthYear=${monthYear}`
        : '';

    const isActive = (path: string) => {
        return pathname === path || pathname.startsWith(path + '/');
    };

    return (
        <>
            <div className="sticky top-0 z-40 border-b bg-background md:ml-72">
                <div className="flex min-h-16 flex-wrap items-center justify-between gap-3 px-4 py-2">
                    <div className="flex min-w-0 flex-1 items-center justify-between gap-3 md:hidden">
                        <Link href={`/${caseSearch}`}
                              className="flex min-w-0 items-center gap-2 hover:opacity-80 transition-opacity">
                            <Briefcase className="h-5 w-5 shrink-0"/>
                            <span className="truncate font-semibold">Schichtplan Manager</span>
                        </Link>

                        <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => setIsMobileOpen(true)}
                            aria-label="Navigation öffnen"
                        >
                            <Menu className="h-5 w-5"/>
                        </Button>
                    </div>

                    <div className="ml-auto flex w-full justify-start md:w-auto md:justify-end">
                        <MonthSelector
                            disabled={isLocked}
                            lockedCaseId={lockedCaseId}
                            lockedMonthYear={lockedMonthYear}
                        />
                    </div>
                </div>
            </div>

            <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 border-r border-sidebar-border md:block">
                <SidebarContent
                    caseSearch={caseSearch}
                    isActive={isActive}
                />
            </aside>

            {isMobileOpen && (
                <div className="fixed inset-0 z-50 md:hidden">
                    <button
                        type="button"
                        className="absolute inset-0 bg-black/40"
                        onClick={() => setIsMobileOpen(false)}
                        aria-label="Navigation schließen"
                    />
                    <aside className="relative h-full w-72 max-w-[85vw] border-r border-sidebar-border shadow-xl">
                        <SidebarContent
                            caseSearch={caseSearch}
                            isActive={isActive}
                            onClose={() => setIsMobileOpen(false)}
                            showCloseButton
                        />
                    </aside>
                </div>
            )}
        </>
    );
}

interface NavigationWrapperProps {
    isLocked: boolean;
    lockedCaseId?: number | null;
    lockedMonthYear?: string | null;
}

export function NavigationWrapper({isLocked, lockedCaseId, lockedMonthYear}: NavigationWrapperProps) {
    return (
        <Suspense fallback={<div className="h-16 border-b bg-background sticky top-0 z-50 md:ml-72"/>}>
            <AppNavigation isLocked={isLocked} lockedCaseId={lockedCaseId} lockedMonthYear={lockedMonthYear} />
        </Suspense>
    );
}
