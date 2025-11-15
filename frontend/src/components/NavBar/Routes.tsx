import { Route } from "react-router-dom";
import type { NavigationItem } from "../../types/navbarTypes";
import ProtectedRoute from "./ProtectedRoute";

export function handleRoutes(navigation: NavigationItem[]) {
  return navigation.flatMap((nav) => {
    // Case 1: Navigation with dropdown
    if (nav.type === "dropdown") {
      return nav.items.map((item) => (
        <Route
          key={item.href}
          path={item.href}
          element={
            <ProtectedRoute allowedRoles={item.allowedRoles ?? ["student"]}>
              {item.element}
            </ProtectedRoute>
          }
        />
      ));
    }

    // Case 2: Single navigation item
    return (
      <Route
        key={nav.href}
        path={nav.href}
        element={
          <ProtectedRoute allowedRoles={nav.allowedRoles}>
            {nav.element}
          </ProtectedRoute>
        }
      />
    );
  });
}
