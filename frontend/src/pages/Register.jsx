import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { extractErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register(form);
      navigate("/login", { state: { registered: true } });
    } catch (err) {
      setError(extractErrorMessage(err, "Could not create your account."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-[80vh] max-w-md flex-col justify-center px-6">
      <h1 className="text-2xl font-semibold text-ink">Create your account</h1>
      <p className="mt-1 text-sm text-ink/60">Register to start managing cards and payments.</p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm font-medium text-ink/80">First name</label>
            <input
              required
              value={form.first_name}
              onChange={update("first_name")}
              className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-ink/80">Last name</label>
            <input
              value={form.last_name}
              onChange={update("last_name")}
              className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
            />
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-ink/80">Email</label>
          <input
            type="email"
            required
            value={form.email}
            onChange={update("email")}
            className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
          />
        </div>

        <div>
          <label className="text-sm font-medium text-ink/80">Password</label>
          <input
            type="password"
            required
            minLength={8}
            value={form.password}
            onChange={update("password")}
            className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
          />
          <p className="mt-1 text-xs text-ink/50">At least 8 characters.</p>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-ledger-500 py-2.5 font-medium text-white transition hover:bg-ledger-600 disabled:opacity-60"
        >
          {submitting ? "Creating account..." : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-ink/60">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-ledger-600 hover:underline">Log in</Link>
      </p>
    </div>
  );
}
