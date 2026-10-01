"use client";

import { Card } from "@/components/ui/card";
import { AlertCircle, AlertTriangle, Calendar, CalendarX, Clock, Moon, TrendingUp, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { ScheduleStats } from "@/entities/models/schedule.model";

interface StatsGridProps {
  stats: ScheduleStats;
}

const statConfig = [
  {
    key: "forward_rotation_violations" as keyof ScheduleStats,
    label: "Vorwärtsrotationsverletzungen",
    icon: TrendingUp,
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
  },
  {
    key: "consecutive_working_days_gt_5" as keyof ScheduleStats,
    label: "Mehr als 5 aufeinanderfolgende Arbeitstage",
    icon: Calendar,
    color: "text-red-500",
    bgColor: "bg-red-500/10",
  },
  {
    key: "no_free_weekend" as keyof ScheduleStats,
    label: "Kein freies Wochenende",
    icon: CalendarX,
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
  },
  {
    key: "consecutive_night_shifts_gt_3" as keyof ScheduleStats,
    label: "Mehr als 3 aufeinanderfolgende Nachtschichten",
    icon: Moon,
    color: "text-indigo-500",
    bgColor: "bg-indigo-500/10",
  },
  {
    key: "total_overtime_hours" as keyof ScheduleStats,
    label: "Gesamtüberstunden (Stunden)",
    icon: Clock,
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
  },
  {
    key: "no_free_days_around_weekend" as keyof ScheduleStats,
    label: "Keine freien Tage um das Wochenende",
    icon: AlertCircle,
    color: "text-pink-500",
    bgColor: "bg-pink-500/10",
  },
  {
    key: "not_free_after_night_shift" as keyof ScheduleStats,
    label: "48h nicht frei nach Nachtschicht",
    icon: AlertTriangle,
    color: "text-rose-500",
    bgColor: "bg-rose-500/10",
  },
  {
    key: "violated_wish_total" as keyof ScheduleStats,
    label: "Verletzte Wünsche",
    icon: XCircle,
    color: "text-red-600",
    bgColor: "bg-red-600/10",
  },
];

/**
 * Displays schedule quality statistics in a grid layout.
 * Each stat is shown in a card with an icon and color coding.
 * Green highlighting is used when a stat value is 0 (optimal).
 */
export function StatsGrid({ stats }: StatsGridProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {statConfig.map(({ key, label, icon: Icon, color, bgColor }) => {
        const value = stats[key];
        const isGood = value === 0;

        return (
          <Card
            key={key}
            className={cn(
              "border-border/50 p-4 transition-all hover:shadow-md",
              isGood && "border-emerald-500/20 bg-emerald-500/5",
            )}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground">{label}</p>
                <p className={cn("mt-2 text-3xl font-bold", isGood ? "text-emerald-500" : color)}>
                  {typeof value === "number" ? value.toFixed(value % 1 === 0 ? 0 : 2) : value}
                </p>
              </div>
              <div className={cn("rounded-lg p-2", isGood ? "bg-emerald-500/10" : bgColor)}>
                <Icon className={cn("h-5 w-5", isGood ? "text-emerald-500" : color)} />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
