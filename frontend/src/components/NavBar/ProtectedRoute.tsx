import { Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import type { AllowedRoles } from "../../api/userAPI";

export default function ProtectedRoute({
    children,
    allowedRoles,
}: {
    children: React.ReactNode;
    allowedRoles: AllowedRoles;
}) {
    const { user, userData } = useAuth();

    // Not logged in
    if (!user || !userData) return <Navigate to="/login" replace />;

    // No role or invalid role
    if (!userData?.role || !allowedRoles.includes(userData.role)) {
        return <Navigate to="/unauthorized" replace />;
    }

    return children;
}
