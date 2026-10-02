import Link from "next/link";
import { CalendarCheck, CalendarHeart, CalendarPlus, UserCog, Users, type LucideIcon } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/page-header";
import { loadPlanningScope, type ScopeSearchParams } from "@/lib/scope";
import { selectionSearch } from "@/lib/selection";
import { cn } from "@/lib/utils";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Schichtplanung" };

interface Area {
  title: string;
  description: string;
  icon: LucideIcon;
  href?: string;
  color: string;
}

const areas: Area[] = [
  {
    title: "Mitarbeiter",
    description: "Mitarbeiter, Zuordnungen, Monatskonten und Einschränkungen der Auswahl prüfen",
    icon: Users,
    href: "/employees",
    color: "text-blue-500 bg-blue-50",
  },
  {
    title: "Verfügbarkeit",
    description: "Einschränkungen und Wünsche einzelner Mitarbeiter im Monat bearbeiten",
    icon: CalendarHeart,
    href: "/availability",
    color: "text-rose-500 bg-rose-50",
  },
  {
    title: "Mindestbesetzung",
    description: "Mindestbesetzung je Tag, Schicht und Qualifikation festlegen",
    icon: UserCog,
    href: "/staffing",
    color: "text-amber-500 bg-amber-50",
  },
  {
    title: "Dienstplan erstellen",
    description: "Einen Dienstplan für den gewählten Monat und die Stationen generieren",
    icon: CalendarPlus,
    color: "text-purple-500 bg-purple-50",
  },
  {
    title: "Dienstplan prüfen",
    description: "Generierte Dienstpläne prüfen, exportieren und veröffentlichen",
    icon: CalendarCheck,
    color: "text-green-500 bg-green-50",
  },
];

export default async function HomePage({ searchParams }: { searchParams: Promise<ScopeSearchParams> }) {
  const scope = await loadPlanningScope("/", await searchParams);
  const search = selectionSearch(scope.month, scope.stationIds);

  return (
    <div className="py-6">
      <PageHeader
        title="Schichtplanung"
        description="Planungsmonat und Stationen wählen, dann die Planungsdaten prüfen."
        scope={scope}
      />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {areas.map(({ title, description, icon: Icon, href, color }) => {
          const card = (
            <Card
              className={cn("h-full gap-0 transition-shadow", href ? "cursor-pointer hover:shadow-lg" : "opacity-60")}
            >
              <CardHeader>
                <div className={cn("w-fit rounded-lg p-3", color)}>
                  <Icon className="h-6 w-6" />
                </div>
                <CardTitle className="mt-4">{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </CardHeader>
              <CardContent className="mt-auto pt-6">
                <span className={cn(buttonVariants({ variant: "outline" }), "w-full", !href && "opacity-50")}>
                  {href ? "Öffnen" : "Noch nicht unterstützt"}
                </span>
              </CardContent>
            </Card>
          );
          return href ? (
            <Link key={title} href={`${href}${search}`} className="rounded-xl">
              {card}
            </Link>
          ) : (
            <div key={title} aria-disabled="true">
              {card}
            </div>
          );
        })}
      </div>
    </div>
  );
}
