import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { extractErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const justRegistered = location.state?.registered;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const user = await login(email, password);
      navigate(user.is_staff ? "/admin" : "/dashboard", { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err, "Invalid email or password."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-[80vh] max-w-md flex-col justify-center px-6">
      <h1 className="text-2xl font-semibold text-ink">Welcome back</h1>
      <p className="mt-1 text-sm text-ink/60">Log in to manage your cards and payments.</p>

      {justRegistered && (
        <p className="mt-4 rounded-md bg-ledger-50 px-3 py-2 text-sm text-ledger-700">
          Account created — you can log in now.
        </p>
      )}

      <form onSubmit={handleSubmit} className="mt-8 space-y-4">
        <div>
          <label className="text-sm font-medium text-ink/80">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
          />
        </div>
        <div>
          <label className="text-sm font-medium text-ink/80">Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
          />
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-ledger-500 py-2.5 font-medium text-white transition hover:bg-ledger-600 disabled:opacity-60"
        >
          {submitting ? "Logging in..." : "Log in"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-ink/60">
        Don't have an account?{" "}
        <Link to="/register" className="font-medium text-ledger-600 hover:underline">Sign up</Link>
      </p>
    </div>
  );
}
