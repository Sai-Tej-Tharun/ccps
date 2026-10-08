import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import ThemeToggle from "./ThemeToggle";

export default function Navbar() {
  const { isAuthenticated, isAdmin, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <nav className="border-b border-ledger-100 bg-paper/95 backdrop-blur sticky top-0 z-10">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-y-3 px-6 py-4">
        <Link to="/" className="font-serif text-lg font-semibold text-ink">
          Ledger<span className="text-ledger-500">Pay</span>
        </Link>

        {isAuthenticated && (
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm font-medium text-ink/80">
            <Link to="/dashboard" className="hover:text-ledger-600">Dashboard</Link>
            <Link to="/cards/add" className="hover:text-ledger-600">Add Card</Link>
            <Link to="/payments/new" className="hover:text-ledger-600">Make Payment</Link>
            <Link to="/transactions" className="hover:text-ledger-600">History</Link>
            {isAdmin && (
              <>
                <Link to="/admin" className="hover:text-ledger-600">Admin</Link>
                <Link to="/admin/cards" className="hover:text-ledger-600">Cards</Link>
              </>
            )}
          </div>
        )}

        <div className="flex items-center gap-4">
          <ThemeToggle />
          {isAuthenticated ? (
            <>
              <span className="hidden text-sm text-ink/60 sm:inline">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="rounded-md border border-ledger-500 px-3 py-1.5 text-sm font-medium text-ledger-600 transition hover:bg-ledger-500 hover:text-white"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-ink/80 hover:text-ledger-600">Login</Link>
              <Link
                to="/register"
                className="rounded-md bg-ledger-500 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-ledger-600"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
