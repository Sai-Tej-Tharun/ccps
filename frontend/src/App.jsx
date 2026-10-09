import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider, useAuth } from "./context/AuthContext";
import AddCard from "./pages/AddCard";
import AdminCards from "./pages/AdminCards";
import AdminDashboard from "./pages/AdminDashboard";
import AdminSecurity from "./pages/AdminSecurity";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import MakePayment from "./pages/MakePayment";
import Register from "./pages/Register";
import TransactionHistory from "./pages/TransactionHistory";

// The charts library is large, so the analytics page is only downloaded when someone opens it.
const Analytics = lazy(() => import("./pages/Analytics"));

function HomeRedirect() {
  const { isAuthenticated, isAdmin, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Navigate to={isAdmin ? "/admin" : "/dashboard"} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />

          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/cards/add" element={<ProtectedRoute><AddCard /></ProtectedRoute>} />
          <Route path="/payments/new" element={<ProtectedRoute><MakePayment /></ProtectedRoute>} />
          <Route path="/transactions" element={<ProtectedRoute><TransactionHistory /></ProtectedRoute>} />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <Suspense fallback={<p className="px-6 py-10 text-center text-sm text-ink/50">Loading charts...</p>}>
                  <Analytics />
                </Suspense>
              </ProtectedRoute>
            }
          />
          <Route path="/admin" element={<ProtectedRoute permission="analytics.view"><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/cards" element={<ProtectedRoute permission="cards.view"><AdminCards /></ProtectedRoute>} />
          <Route path="/admin/security" element={<ProtectedRoute permission="fraud.view"><AdminSecurity /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </AuthProvider>
  );
}
