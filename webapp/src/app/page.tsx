import Link from "next/link";
import { CalendarCheck, CalendarHeart, CalendarPlus, Sparkles, UserCog, Users, type LucideIcon } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/page-header";
import { areaColors } from "@/lib/area-colors";
import { loadPlanningScope, type ScopeSearchParams } from "@/lib/scope";
import { selectionSearch } from "@/lib/selection";
import { cn } from "@/lib/utils";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Übersicht · Schichtplan Manager" };

interface Area {
  title: string;
  description: string;
  icon: LucideIcon;
  href: string;
  color: string;
}

const areas: Area[] = [
  {
    title: "Mitarbeiter",
    description: "Mitarbeiter der Auswahl mit Zuordnungen, Monatskonten und Verfügbarkeit ansehen",
    icon: Users,
    href: "/employees",
    color: areaColors.employees.icon,
  },
  {
    title: "Verfügbarkeit",
    description: "Einschränkungen und Wünsche einzelner Mitarbeiter im Monat bearbeiten",
    icon: CalendarHeart,
    href: "/availability",
    color: areaColors.availability.icon,
  },
  {
    title: "Mindestbesetzung",
    description: "Benötigtes Personal je Station, Tag, Schicht und Qualifikation festlegen",
    icon: UserCog,
    href: "/staffing",
    color: areaColors.staffing.icon,
  },
  {
    title: "Dienstplan erstellen",
    description: "Einen Dienstplan für den ganzen Monat der gewählten Stationen generieren",
    icon: CalendarPlus,
    href: "/generation",
    color: areaColors.createRoster.icon,
  },
  {
    title: "Dienstplan prüfen",
    description: "Den erstellten oder importierten Dienstplan prüfen und in TimeOffice veröffentlichen",
    icon: CalendarCheck,
    href: "/review",
    color: areaColors.reviewRoster.icon,
  },
];

export default async function HomePage({ searchParams }: { searchParams: Promise<ScopeSearchParams> }) {
  const scope = await loadPlanningScope("/", await searchParams);
  const search = selectionSearch(scope.month, scope.stationIds);

  return (
    <div className="py-6">
      <PageHeader title="Übersicht" scope={scope} />

      <section
        aria-labelledby="welcome-title"
        className="mb-6 flex gap-4 rounded-xl border border-sky-200 bg-gradient-to-r from-sky-50 to-emerald-50 p-6 dark:border-sky-900 dark:from-sky-950 dark:to-emerald-950"
      >
        <div className="hidden h-fit rounded-lg bg-background/70 p-3 text-sky-700 sm:block" aria-hidden>
          <Sparkles className="h-6 w-6" />
        </div>
        <div className="space-y-1.5">
          <h2 id="welcome-title" className="text-lg font-semibold">
            Willkommen beim Schichtplan Manager
          </h2>
          <p className="max-w-3xl text-muted-foreground">
            Hier planen Sie den Dienstplan Ihrer Stationen für einen ganzen Monat: Mitarbeiter ansehen, Verfügbarkeit
            und Mindestbesetzung pflegen, einen Dienstplan erstellen lassen, ihn prüfen und in TimeOffice
            veröffentlichen. Wählen Sie oben Monat und Stationen; jede Seite arbeitet mit dieser Auswahl.
          </p>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {areas.map(({ title, description, icon: Icon, href, color }) => (
          <Link key={title} href={`${href}${search}`} className="rounded-xl">
            <Card className="h-full cursor-pointer gap-0 transition-shadow hover:shadow-lg focus-within:shadow-lg">
              <CardHeader>
                <div className={cn("w-fit rounded-lg p-3", color)}>
                  <Icon className="h-6 w-6" />
                </div>
                <CardTitle className="mt-4">{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
