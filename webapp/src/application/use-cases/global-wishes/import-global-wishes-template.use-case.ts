export interface IImportGlobalWishesTemplateUseCase {
  (input: {
    caseId: number;
    monthYear: string;
    templateId: string;
  }): Promise<{ matchCount: number; totalCount: number; unmatchedCount: number }>;
}
export function makeImportGlobalWishesTemplateUseCase(): IImportGlobalWishesTemplateUseCase {
  return async () => {
    throw new Error("Wiederkehrende Vorlagen werden noch nicht unterstützt.");
  };
}
