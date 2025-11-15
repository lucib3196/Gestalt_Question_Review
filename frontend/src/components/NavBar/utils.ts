
import type { UserRole } from "../../api/userAPI";
import type { NavigationItem } from "../../types/navbarTypes";
import type { User } from "firebase/auth";

export function canAccessRoute(
  nav: NavigationItem,
  user: User | null,
  userRole: UserRole
) {
  if (nav.requiresAuth && !user) return false;

  // Route has role restrictions
  if (nav.allowedRoles && nav.allowedRoles.length > 0) {
    if (!userRole) return false;
    return nav.allowedRoles.includes(userRole);
  }

  // Public OR only requires login
  return true;
}
