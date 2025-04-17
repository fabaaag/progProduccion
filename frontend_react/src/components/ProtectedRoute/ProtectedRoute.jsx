import { Navigate } from "react-router-dom";
import { checkAuthStatus } from "../../api/auth.api";

export function ProtectedRoute({ children, allowedRoles = [] }) {
    const { isAuthenticated, user } = checkAuthStatus();

    if (!isAuthenticated) {
        return <Navigate to="/login" />;
    }

    //Si se especifican roles permitidos, verificar si el usuario tiene acceso
    if (allowedRoles.length > 0 && !allowedRoles.includes(user?.rol)){
        return <Navigate to="/home" />;
    }

    return children;
}