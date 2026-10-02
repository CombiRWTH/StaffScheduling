"use client";

import { usePathname, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense, useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Briefcase,
  CalendarHeart,
  CalendarCheck,
  CalendarPlus,
  FileText,
  type LucideIcon,
  Menu,
  Repeat,
  UserCog,
  Users,
  X,
} from "lucide-react";
import { type AreaColor, areaColors } from "@/lib/area-colors";
import { selectionSearch } from "@/lib/selection";
import { cn } from "@/lib/utils";

/** Links without `href` are discoverable but not yet supported by the canonical backend. */
interface NavigationLink {
  label: string;
  icon: LucideIcon;
  href?: string;
  /** What the entry covers, shown as a tooltip. */
  hint?: string;
  /** Highlight of the current entry, matching the area's home card. */
  color?: AreaColor;
}

const navigationSections: Array<{ label: string; links: NavigationLink[] }> = [
  {
    label: "Planungsdaten",
    links: [
      { href: "/employees", label: "Mitarbeiter", icon: Users, color: areaColors.employees },
      {
        href: "/availability",
        label: "Verfügbarkeit",
        icon: CalendarHeart,
        hint: "Einschränkungen und Wünsche des Monats",
        color: areaColors.availability,
      },
      { href: "/staffing", label: "Mindestbesetzung", icon: UserCog, color: areaColors.staffing },
    ],
  },
  {
    label: "Wiederkehrend",
    links: [
      { label: "Verfügbarkeit", icon: Repeat, hint: "Wiederkehrende Wünsche und Einschränkungen" },
      { label: "Vorlagen", icon: FileText },
    ],
  },
  {
    label: "Dienstplan",
    links: [
      { href: "/generation", label: "Erstellen", icon: CalendarPlus, color: areaColors.createRoster },
      { label: "Prüfen", icon: CalendarCheck },
    ],
  },
];

interface SidebarContentProps {
  search: string;
  isActive: (path: string) => boolean;
  onClose?: () => void;
  showCloseButton?: boolean;
}

function SidebarContent({ search, isActive, onClose, showCloseButton = false }: SidebarContentProps) {
  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex h-16 shrink-0 items-center justify-between gap-3 border-b border-sidebar-border px-6">
        <Link
          href={`/${search}`}
          className="flex min-w-0 items-center gap-2 hover:opacity-80 transition-opacity"
          onClick={onClose}
        >
          <Briefcase className="h-5 w-5 shrink-0" />
          <span className="truncate font-semibold">Schichtplan Manager</span>
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
            <X className="h-5 w-5" />
          </Button>
        )}
      </div>

      <ScrollArea className="min-h-0 flex-1">
        <nav className="space-y-4 px-3 py-3">
          {navigationSections.map(({ label, links }) => (
            <section key={label} className="flex flex-col gap-0.5">
              <h2 className="px-3 pb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</h2>
              {links.map(({ href, label: linkLabel, icon: Icon, hint, color }) =>
                !href ? (
                  <div
                    key={linkLabel}
                    aria-disabled="true"
                    title={hint ? `${hint} – noch nicht unterstützt` : "Noch nicht unterstützt"}
                    className="flex h-8 cursor-not-allowed items-center gap-2.5 rounded-md px-3 text-sm text-muted-foreground/60"
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="truncate">{linkLabel}</span>
                    <span className="sr-only">(noch nicht unterstützt)</span>
                  </div>
                ) : (
                  <Button
                    key={href}
                    variant="ghost"
                    asChild
                    className={cn(
                      "h-8 w-full justify-start gap-2.5 px-3 font-normal",
                      isActive(href)
                        ? cn("font-medium", color?.navActive ?? "bg-sidebar-accent text-sidebar-accent-foreground")
                        : "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                    )}
                  >
                    <Link href={`${href}${search}`} onClick={onClose} title={hint}>
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className="truncate">{linkLabel}</span>
                    </Link>
                  </Button>
                ),
              )}
            </section>
          ))}
        </nav>
      </ScrollArea>
    </div>
  );
}

export function AppNavigation() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const search = selectionSearch(searchParams.get("month"), searchParams.get("stations"));

  const isActive = (path: string) => {
    return pathname === path || pathname.startsWith(path + "/");
  };

  return (
    <>
      <div className="sticky top-0 z-40 flex h-14 items-center justify-between border-b bg-background px-4 md:hidden">
        <Link href={`/${search}`} className="flex items-center gap-2 font-semibold">
          <Briefcase className="h-5 w-5" />
          Schichtplan Manager
        </Link>
        <Button variant="ghost" size="icon" onClick={() => setIsMobileOpen(true)} aria-label="Navigation öffnen">
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      <aside className="sticky top-0 z-40 hidden h-screen w-max max-w-72 shrink-0 border-r border-sidebar-border md:block">
        <SidebarContent search={search} isActive={isActive} />
      </aside>

      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => setIsMobileOpen(false)}
            aria-label="Navigation schließen"
          />
          <aside className="relative h-full w-max max-w-[85vw] border-r border-sidebar-border shadow-xl">
            <SidebarContent
              search={search}
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

/** useSearchParams requires a Suspense boundary during prerendering. */
export function NavigationWrapper() {
  return (
    <Suspense>
      <AppNavigation />
    </Suspense>
  );
}
