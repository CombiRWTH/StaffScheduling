import { z } from "zod";

export const WeightTypeSchema = z.enum([
  "free_weekend",
  "consecutive_nights",
  "hidden",
  "overtime",
  "consecutive_days",
  "rotate",
  "wishes",
  "after_night",
  "second_weekend",
  "fairness",
]);

export type WeightType = z.infer<typeof WeightTypeSchema>;

export const WeightMetadataSchema = z.object({
  key: WeightTypeSchema,
  label: z.string(),
  description: z.string(),
});

export type WeightMetadata = z.infer<typeof WeightMetadataSchema>;

export const WeightsSchema = z.object({
  free_weekend: z.number(),
  consecutive_nights: z.number(),
  hidden: z.number(),
  overtime: z.number(),
  consecutive_days: z.number(),
  rotate: z.number(),
  wishes: z.number(),
  after_night: z.number(),
  second_weekend: z.number(),
  fairness: z.number(),
});

export type Weights = z.infer<typeof WeightsSchema>;

export const WEIGHT_METADATA: WeightMetadata[] = [
  {
    key: "free_weekend",
    label: "Freie Tage am Wochenende",
    description: "Freie Tage nahe am Wochenende bevorzugen",
  },
  {
    key: "consecutive_nights",
    label: "Aufeinanderfolgende Nachtschichten",
    description: "Aufeinanderfolgende Nachtschichten minimieren",
  },
  /* Hidden employees are no longer used. Keep this entry for later restoration.
    {
        key: 'hidden',
        label: 'Versteckte Mitarbeiter',
        description: 'Sicherstellen, dass alle qualifizierten Mitarbeiter eingeplant werden',
    },
    */
  {
    key: "overtime",
    label: "Überstunden",
    description: "Überstunden aller Mitarbeiter minimieren",
  },
  {
    key: "consecutive_days",
    label: "Aufeinanderfolgende Arbeitstage",
    description: "Aufeinanderfolgende Arbeitstage begrenzen",
  },
  {
    key: "rotate",
    label: "Schichten vorwärts rotieren",
    description: "Vorwärtsrotation der Schichten fördern (F→S→N)",
  },
  {
    key: "wishes",
    label: "Mitarbeiterwünsche",
    description: "Wünsche der Mitarbeiter berücksichtigen",
  },
  {
    key: "after_night",
    label: "Freier Tag nach Nachtschicht",
    description: "Ruhetag nach Nachtschichtphase sicherstellen",
  },
  {
    key: "second_weekend",
    label: "Jedes zweite Wochenende frei",
    description: "Abwechselnde freie Wochenenden anstreben",
  },
  {
    key: "fairness",
    label: "Fairness",
    description: "Faire Verteilung von Schichten und Belastung zwischen Mitarbeitern",
  },
];

export const DEFAULT_WEIGHTS: Weights = {
  free_weekend: 2,
  consecutive_nights: 2,
  hidden: 0,
  overtime: 4,
  consecutive_days: 1,
  rotate: 1,
  wishes: 3,
  after_night: 3,
  second_weekend: 1,
  fairness: 3,
};
