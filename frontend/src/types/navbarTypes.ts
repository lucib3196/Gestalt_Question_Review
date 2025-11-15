import type { AllowedRoles } from "../api/userAPI";

export type BaseNavRoutes = {
  name: string;
  includeNavBar?: boolean;
  requiresAuth: boolean;
  allowedRoles: AllowedRoles;
};

export type SingleNavRoute = BaseNavRoutes & {
  type: "route";
  href: string;
  element: React.ReactNode;
};

export type DropDownNavRoute = BaseNavRoutes & {
  type: "dropdown";
  items: {
    name: string;
    href: string;
    element: React.ReactNode;
    allowedRoles?: AllowedRoles;
    requiresAuth?: boolean;
  }[];
};

export type NavigationItem = SingleNavRoute | DropDownNavRoute;
