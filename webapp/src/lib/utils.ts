import {type ClassValue, clsx} from "clsx"
import {twMerge} from "tailwind-merge"

/**
 * Utility function for merging Tailwind CSS classes.
 * Combines clsx for conditional class names with tailwind-merge to resolve conflicts.
 *
 * This function is useful for creating dynamic class names while avoiding Tailwind
 * class conflicts (e.g., when multiple classes affect the same CSS property).
 *
 * @param inputs - Class values to merge (strings, objects, arrays)
 * @returns A single string with merged and deduplicated Tailwind classes
 *
 * @example
 * cn('px-2 py-1', 'px-4') // Returns: 'py-1 px-4' (px-4 overrides px-2)
 * cn('text-red-500', { 'text-blue-500': isActive }) // Conditional classes
 * cn(['flex', 'items-center'], 'justify-between') // Array support
 */
export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}
