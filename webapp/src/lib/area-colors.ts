/**
 * Per-area accent colors shared by the home cards and the navigation.
 * Class names stay literal so Tailwind's scanner picks them up.
 */
export interface AreaColor {
  /** Tinted icon tile on the home page. */
  icon: string;
  /** Highlight of the current navigation entry. */
  navActive: string;
}

export const areaColors = {
  employees: {
    icon: "text-blue-500 bg-blue-50",
    navActive: "bg-blue-100/80 text-blue-700 hover:bg-blue-100 hover:text-blue-800",
  },
  availability: {
    icon: "text-rose-500 bg-rose-50",
    navActive: "bg-rose-100/80 text-rose-700 hover:bg-rose-100 hover:text-rose-800",
  },
  staffing: {
    icon: "text-amber-500 bg-amber-50",
    navActive: "bg-amber-100/80 text-amber-700 hover:bg-amber-100 hover:text-amber-800",
  },
  createRoster: {
    icon: "text-purple-500 bg-purple-50",
    navActive: "bg-purple-100/80 text-purple-700 hover:bg-purple-100 hover:text-purple-800",
  },
  reviewRoster: {
    icon: "text-green-500 bg-green-50",
    navActive: "bg-green-100/80 text-green-700 hover:bg-green-100 hover:text-green-800",
  },
} satisfies Record<string, AreaColor>;
