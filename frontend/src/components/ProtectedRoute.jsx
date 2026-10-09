import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children, adminOnly = false, permission = null }) {
  const { isAuthenticated, isAdmin, can, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="flex min-h-[60vh] items-center justify-center text-ledger-600">Loading...</div>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if ((adminOnly && !isAdmin) || (permission && !can(permission))) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}
