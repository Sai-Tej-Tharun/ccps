import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchDailySummary } from "../api/admin";

export default function AdminDashboard() {
  const [summary, setSummary] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDailySummary(14)
      .then(setSummary)
      .finally(() => setLoading(false));
  }, []);

  const totals = summary.reduce(
    (acc, row) => ({
      total: acc.total + row.total_count,
      success: acc.success + row.success_count,
      failed: acc.failed + row.failed_count,
      amount: acc.amount + Number(row.total_success_amount),
    }),
    { total: 0, success: 0, failed: 0, amount: 0 }
  );

  const maxCount = Math.max(1, ...summary.map((r) => r.total_count));

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-ink">Admin Dashboard</h1>
        <Link to="/transactions" className="text-sm font-medium text-ledger-600 hover:underline">View all transactions →</Link>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-4">
        <SummaryCard label="Transactions (14d)" value={totals.total} />
        <SummaryCard label="Successful" value={totals.success} tone="success" />
        <SummaryCard label="Failed" value={totals.failed} tone="danger" />
        <SummaryCard label="Volume" value={`$${totals.amount.toFixed(2)}`} />
      </div>

      <div className="mt-8 rounded-xl border border-ink/10 bg-white p-6">
        <h2 className="font-serif text-lg text-ink">Daily Payment Summary</h2>
        {loading ? (
          <p className="mt-4 text-sm text-ink/50">Loading...</p>
        ) : summary.length === 0 ? (
          <p className="mt-4 text-sm text-ink/50">No transactions in the selected period.</p>
        ) : (
          <div className="mt-6 space-y-3">
            {summary.map((row) => (
              <div key={row.date} className="flex items-center gap-3 text-sm">
                <span className="w-24 shrink-0 text-ink/60">{row.date}</span>
                <div className="h-3 flex-1 overflow-hidden rounded-full bg-ink/5">
                  <div
                    className="h-full rounded-full bg-ledger-500"
                    style={{ width: `${(row.total_count / maxCount) * 100}%` }}
                  />
                </div>
                <span className="w-10 text-right text-ink/70">{row.total_count}</span>
                <span className="amount w-24 text-right text-ink/60">${row.total_success_amount}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SummaryCard({ label, value, tone }) {
  const toneClass = tone === "success" ? "text-ledger-600" : tone === "danger" ? "text-danger" : "text-ink";
  return (
    <div className="rounded-xl border border-ink/10 bg-white p-5">
      <p className="text-xs uppercase tracking-wide text-ink/50">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}
