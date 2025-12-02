import { Card } from "@/components/ui/card"
import { AlertTriangle, Clock, Calendar, Moon, TrendingUp, AlertCircle, CalendarX, XCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface StatsGridProps {
  stats: {
    forward_rotation_violations: number
    consecutive_working_days_gt_5: number
    no_free_weekend: number
    consecutive_night_shifts_gt_3: number
    total_overtime_hours: number
    no_free_days_around_weekend: number
    not_free_after_night_shift: number
    violated_wish_total: number
  }
}

const statConfig = [
  {
    key: "forward_rotation_violations",
    label: "Forward Rotation Violations",
    icon: TrendingUp,
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
  },
  {
    key: "consecutive_working_days_gt_5",
    label: "Consecutive Days > 5",
    icon: Calendar,
    color: "text-red-500",
    bgColor: "bg-red-500/10",
  },
  {
    key: "no_free_weekend",
    label: "No Free Weekend",
    icon: CalendarX,
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
  },
  {
    key: "consecutive_night_shifts_gt_3",
    label: "Night Shifts > 3",
    icon: Moon,
    color: "text-indigo-500",
    bgColor: "bg-indigo-500/10",
  },
  {
    key: "total_overtime_hours",
    label: "Total Overtime Hours",
    icon: Clock,
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
  },
  {
    key: "no_free_days_around_weekend",
    label: "No Free Days Around Weekend",
    icon: AlertCircle,
    color: "text-pink-500",
    bgColor: "bg-pink-500/10",
  },
  {
    key: "not_free_after_night_shift",
    label: "48h Not Free After Night",
    icon: AlertTriangle,
    color: "text-rose-500",
    bgColor: "bg-rose-500/10",
  },
  {
    key: "violated_wish_total",
    label: "Violated Wishes",
    icon: XCircle,
    color: "text-red-600",
    bgColor: "bg-red-600/10",
  },
]

export function StatsGrid({ stats }: StatsGridProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {statConfig.map(({ key, label, icon: Icon, color, bgColor }) => {
        const value = stats[key as keyof typeof stats]
        const isGood = value === 0

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
        )
      })}
    </div>
  )
}
