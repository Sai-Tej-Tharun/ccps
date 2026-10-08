import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDashboardSummary } from "../api/dashboard";
import { extractErrorMessage } from "../api/client";
import StatementDownload from "../components/StatementDownload";
import StatusBadge from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";

const money = (value, currency = "USD") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency }).format(Number(value) || 0);

const formatDate = (iso) => {
  // The API sends naive UTC timestamps; append "Z" so the browser converts to local time.
  const d = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : `${iso}Z`);
  return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
};

function StatCard({ label, value, hint }) {
  return (
    <div className="rounded-xl border border-ink/10 bg-white p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-ink/50">{label}</p>
      <p className="amount mt-2 text-2xl font-semibold text-ink">{value}</p>
      {hint && <p className="mt-1 text-xs text-ink/50">{hint}</p>}
    </div>
  );
}

function StatCardSkeleton() {
  return (
    <div className="animate-pulse rounded-xl border border-ink/10 bg-white p-5">
      <div className="h-3 w-24 rounded bg-ink/10" />
      <div className="mt-4 h-7 w-32 rounded bg-ink/10" />
      <div className="mt-3 h-3 w-20 rounded bg-ink/5" />
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="mt-4 animate-pulse space-y-3">
      {[0, 1, 2, 3, 4].map((i) => (
        <div key={i} className="flex items-center justify-between gap-4 border-t border-ink/5 pt-3">
          <div className="h-4 w-1/4 rounded bg-ink/10" />
          <div className="h-4 w-1/5 rounded bg-ink/10" />
          <div className="h-4 w-1/6 rounded bg-ink/10" />
          <div className="h-5 w-16 rounded-full bg-ink/10" />
        </div>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // { kind: "auth" | "other", message }

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getDashboardSummary()
      .then(setSummary)
      .catch((err) => {
        if (err?.response?.status === 401) {
          setError({
            kind: "auth",
            message: "Your session is invalid or has expired (JWT authentication failed). Please log in again.",
          });
        } else {
          setError({ kind: "other", message: extractErrorMessage(err, "Could not load your dashboard.") });
        }
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  const txns = summary?.last_5_transactions ?? [];

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink">Welcome, {user?.first_name || user?.email}</h1>
          <p className="mt-1 text-ink/60">Here's a quick look at your card usage.</p>
        </div>
        <div className="flex gap-3 text-sm font-medium">
          <Link to="/cards/add" className="rounded-md border border-ledger-500 px-3 py-1.5 text-ledger-600 hover:bg-ledger-50">
            + Add card
          </Link>
          <Link to="/payments/new" className="rounded-md bg-ledger-500 px-3 py-1.5 text-white hover:bg-ledger-600">
            New payment
          </Link>
        </div>
      </div>

      {error && (
        <div role="alert" className="mt-8 rounded-xl border border-red-200 bg-red-50 p-5 text-danger">
          <p className="font-semibold">{error.kind === "auth" ? "Authentication failed" : "Something went wrong"}</p>
          <p className="mt-1 text-sm">{error.message}</p>
          <div className="mt-4 flex gap-3 text-sm font-medium">
            {error.kind === "auth" ? (
              <Link to="/login" className="rounded-md bg-danger px-3 py-1.5 text-white hover:opacity-90">
                Go to login
              </Link>
            ) : (
              <button onClick={load} className="rounded-md bg-danger px-3 py-1.5 text-white hover:opacity-90">
                Try again
              </button>
            )}
          </div>
        </div>
      )}

      {!error && (
        <>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {loading || !summary ? (
              [0, 1, 2, 3].map((i) => <StatCardSkeleton key={i} />)
            ) : (
              <>
                <StatCard label="Total spent" value={money(summary.total_amount_spent)} hint="Successful payments" />
                <StatCard label="Available credit" value={money(summary.available_credit_limit)} hint="Limit minus this month" />
                <StatCard label="Total transactions" value={summary.total_transactions} hint="All attempts" />
                <StatCard label="This month" value={money(summary.current_month_spending)} hint="Spent since the 1st" />
              </>
            )}
          </div>

          <div className="mt-8 rounded-xl border border-ink/10 bg-white p-6">
            <div className="flex items-center justify-between">
              <h2 className="font-serif text-lg text-ink">Last 5 transactions</h2>
              <Link to="/transactions" className="text-sm font-medium text-ledger-600 hover:underline">
                View all →
              </Link>
            </div>

            {loading || !summary ? (
              <TableSkeleton />
            ) : txns.length === 0 ? (
              <p className="mt-4 text-sm text-ink/50">No transactions yet.</p>
            ) : (
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-ink/50">
                      <th className="pb-2 font-medium">Date</th>
                      <th className="pb-2 font-medium">Card</th>
                      <th className="pb-2 font-medium">Amount</th>
                      <th className="pb-2 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {txns.map((t, i) => (
                      <tr key={`${t.date}-${i}`} className="border-t border-ink/5">
                        <td className="py-3 text-ink/60">{formatDate(t.date)}</td>
                        <td className="amount py-3 text-ink/80">{t.masked_card_number || "Card removed"}</td>
                        <td className="amount py-3 text-ink">{money(t.amount, t.currency)}</td>
                        <td className="py-3"><StatusBadge status={t.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          <StatementDownload />
        </>
      )}
    </div>
  );
}