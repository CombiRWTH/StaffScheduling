/**
 * Standard result type for server actions.
 *
 * Mutation server actions must return this type instead of throwing so that
 * client components can handle errors gracefully without relying on try/catch
 * or the global error boundary.
 *
 * @example
 * ```ts
 * // In a client component:
 * const result = await deleteWishesAction(caseId, monthYear, id);
 * if (!result.success) {
 *   toast.error(result.error);
 *   return;
 * }
 * toast.success('Deleted');
 * ```
 */
export type ActionResult<T = undefined> =
    | { success: true; data: T }
    | { success: false; error: string; errorCode?: string };
