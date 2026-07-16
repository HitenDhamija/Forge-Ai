import type { LucideIcon } from "lucide-react";

export interface NavigationItem {
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: string | number;
  disabled?: boolean;
  children?: NavigationItem[];
}

export interface Breadcrumb {
  label: string;
  href?: string;
}

export interface SelectOption {
  label: string;
  value: string;
  disabled?: boolean;
}

export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
}
