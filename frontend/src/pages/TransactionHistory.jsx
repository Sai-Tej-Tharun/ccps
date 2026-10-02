import { useEffect, useState } from "react";
import { downloadTransactionsCsv, listTransactions } from "../api/transactions";
import StatusBadge from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";

const EMPTY_FILTERS = { status: "", date_from: "", date_to: "", min_amount: "", max_amount: "" };

export default function TransactionHistory() {
  const { isAdmin } = useAuth();
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const load = (activeFilters) => {
    setLoading(true);
    const cleaned = Object.fromEntries(Object.entries(activeFilters).filter(([, v]) => v !== ""));
    listTransactions(cleaned)
      .then(setTransactions)
      .finally(() => setLoading(false));
  };

  useEffect(() => load(filters), []); // eslint-disable-line react-hooks/exhaustive-deps

  const update = (field) => (e) => setFilters((f) => ({ ...f, [field]: e.target.value }));

  const applyFilters = (e) => {
    e.preventDefault();
    load(filters);
  };

  const clearFilters = () => {
    setFilters(EMPTY_FILTERS);
    load(EMPTY_FILTERS);
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      await downloadTransactionsCsv(Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== "")));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-ink">{isAdmin ? "All Transactions" : "Transaction History"}</h1>
        {isAdmin && (
          <button
            onClick={handleExport}
            disabled={exporting}
            className="rounded-md border border-ledger-500 px-3 py-1.5 text-sm font-medium text-ledger-600 hover:bg-ledger-500 hover:text-white disabled:opacity-60"
          >
            {exporting ? "Exporting..." : "Export CSV"}
          </button>
        )}
      </div>

      <form onSubmit={applyFilters} className="mt-6 grid grid-cols-2 gap-3 rounded-xl border border-ink/10 bg-white p-5 sm:grid-cols-5">
        <div>
          <label className="text-xs font-medium text-ink/60">Status</label>
          <select value={filters.status} onChange={update("status")} className="mt-1 w-full rounded-md border border-ink/15 px-2 py-1.5 text-sm">
            <option value="">Any</option>
            <option value="SUCCESS">Success</option>
            <option value="FAILED">Failed</option>
            <option value="PENDING">Pending</option>
          </select>
        </div>
        <div>
          <label className="text-xs font-medium text-ink/60">From</label>
          <input type="date" value={filters.date_from} onChange={update("date_from")} className="mt-1 w-full rounded-md border border-ink/15 px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="text-xs font-medium text-ink/60">To</label>
          <input type="date" value={filters.date_to} onChange={update("date_to")} className="mt-1 w-full rounded-md border border-ink/15 px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="text-xs font-medium text-ink/60">Min amount</label>
          <input type="number" step="0.01" value={filters.min_amount} onChange={update("min_amount")} className="mt-1 w-full rounded-md border border-ink/15 px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="text-xs font-medium text-ink/60">Max amount</label>
          <input type="number" step="0.01" value={filters.max_amount} onChange={update("max_amount")} className="mt-1 w-full rounded-md border border-ink/15 px-2 py-1.5 text-sm" />
        </div>
        <div className="col-span-2 flex items-end gap-2 sm:col-span-5">
          <button type="submit" className="rounded-md bg-ledger-500 px-4 py-1.5 text-sm font-medium text-white hover:bg-ledger-600">Apply filters</button>
          <button type="button" onClick={clearFilters} className="rounded-md border border-ink/15 px-4 py-1.5 text-sm font-medium text-ink/70 hover:bg-ink/5">Clear</button>
        </div>
      </form>

      <div className="mt-6 overflow-x-auto rounded-xl border border-ink/10 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ink/10 text-left text-xs uppercase tracking-wide text-ink/50">
              <th className="px-4 py-3">Date</th>
              {isAdmin && <th className="px-4 py-3">User</th>}
              <th className="px-4 py-3">Card</th>
              <th className="px-4 py-3">Amount</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink/50">Loading...</td></tr>
            ) : transactions.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink/50">No transactions match these filters.</td></tr>
            ) : (
              transactions.map((t) => (
                <tr key={t.id} className="border-b border-ink/5 last:border-0">
                  <td className="px-4 py-3 text-ink/70">{new Date(t.created_at).toLocaleString()}</td>
                  {isAdmin && <td className="px-4 py-3 text-ink/70">{t.user_email}</td>}
                  <td className="px-4 py-3 text-ink/70">{t.card_brand ? `${t.card_brand} •••• ${t.card_last4}` : "—"}</td>
                  <td className="amount px-4 py-3 text-ink">{t.currency} {t.amount}</td>
                  <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
