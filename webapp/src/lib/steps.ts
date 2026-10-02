import { CalendarCheck, CalendarHeart, CalendarPlus, UserCog, Users, type LucideIcon } from "lucide-react";
import { areaColors } from "@/lib/area-colors";

export interface Step {
  title: string;
  description: string;
  icon: LucideIcon;
  href: string;
  /** Tinted icon tile on the overview. */
  color: string;
}

/** The planning steps in their usual order; the overview lists them and each page links the next one. */
export const steps = [
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
    description: "Den erstellten oder importierten Dienstplan prüfen, herunterladen und in TimeOffice veröffentlichen",
    icon: CalendarCheck,
    href: "/review",
    color: areaColors.reviewRoster.icon,
  },
] as const satisfies readonly Step[];
