// ============= frontend/lib/utils.ts =============
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: number): string {
  return new Intl.NumberFormat('fa-IR').format(price);
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('fa-IR').format(new Date(date));
}

