import { useEffect, useRef, useState } from "react";
import { extractErrorMessage } from "../api/client";
import { downloadTransactionsCsv, searchTransactions } from "../api/transactions";
import Pagination from "../components/Pagination";
import StatusBadge from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";

const EMPTY_FILTERS = {
  status: "", category: "", fraud_status: "", card: "",
  date_from: "", date_to: "", min_amount: "", max_amount: "",
};
const CATEGORIES = [
  ["SHOPPING", "Shopping"], ["FOOD", "Food & dining"], ["TRAVEL", "Travel"], ["BILLS", "Bills & utilities"],
  ["ENTERTAINMENT", "Entertainment"], ["HEALTH", "Health"], ["OTHER", "Other"],
];
const clean = (filters) => Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== ""));

function validate(f) {
  if (f.date_from && f.date_to && f.date_from > f.date_to) return "'From' date must not be after 'To' date.";
  if (f.min_amount !== "" && f.max_amount !== "" && Number(f.min_amount) > Number(f.max_amount)) {
    return "Minimum amount must not be greater than the maximum.";
  }
  if (f.card && !/\d/.test(f.card)) return "Enter at least one digit of the card number, e.g. 4242.";
  return "";
}

function SortHeader({ label, field, ordering, onSort }) {
  const active = ordering === field || ordering === `-${field}`;
  const descending = ordering === `-${field}`;
  return (
    <th scope="col" aria-sort={active ? (descending ? "descending" : "ascending") : "none"} className="px-4 py-3 text-left">
      <button type="button" onClick={() => onSort(field)} className="inline-flex items-center gap-1 uppercase tracking-wide hover:text-ink">
        {label}
        <span aria-hidden="true">{active ? (descending ? "▼" : "▲") : "↕"}</span>
      </button>
    </th>
  );
}

export default function TransactionHistory() {
  const { can } = useAuth();
  const seesAll = can("transactions.view_all");
  const [draft, setDraft] = useState(EMPTY_FILTERS); // what is typed in the form
  const [applied, setApplied] = useState(EMPTY_FILTERS); // what the table is using
  const [ordering, setOrdering] = useState("-created_at");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [data, setData] = useState({ count: 0, results: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [exporting, setExporting] = useState(false);
  const latest = useRef(0);

  useEffect(() => {
    const requestId = ++latest.current;
    setLoading(true);
    setError("");
    searchTransactions({ ...clean(applied), ordering, page, page_size: pageSize })
      .then((d) => requestId === latest.current && setData(d))
      .catch((err) => {
        if (requestId !== latest.current) return;
        if (err?.response?.status === 404 && page > 1) setPage(1); // the last page vanished after a filter change
        else setError(extractErrorMessage(err, "Could not load transactions."));
      })
      .finally(() => requestId === latest.current && setLoading(false));
  }, [applied, ordering, page, pageSize]);

  const update = (field) => (e) => setDraft((f) => ({ ...f, [field]: e.target.value }));

  const applyFilters = (e) => {
    e.preventDefault();
    const problem = validate(draft);
    setFormError(problem);
    if (problem) return;
    setPage(1);
    setApplied(draft);
  };

  const clearFilters = () => {
    setDraft(EMPTY_FILTERS);
    setApplied(EMPTY_FILTERS);
    setFormError("");
    setPage(1);
  };

  const sortBy = (field) => {
    setPage(1);
    setOrdering((current) => (current === field ? `-${field}` : field));
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      await downloadTransactionsCsv(clean(applied));
    } catch (err) {
      setError(extractErrorMessage(err, "Export failed."));
    } finally {
      setExporting(false);
    }
  };

  const input = "mt-1 w-full rounded-md border border-ink/15 px-2 py-1.5 text-sm";
  const columns = 4 + (seesAll ? 2 : 0);

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-ink">{seesAll ? "All Transactions" : "Transaction History"}</h1>
        {can("transactions.export") && (
          <button
            onClick={handleExport}
            disabled={exporting}
            className="rounded-md border border-ledger-500 px-3 py-1.5 text-sm font-medium text-ledger-600 hover:bg-ledger-500 hover:text-white disabled:opacity-60"
          >
            {exporting ? "Exporting..." : "Export CSV"}
          </button>
        )}
      </div>

      <form onSubmit={applyFilters} className="mt-6 grid grid-cols-2 gap-3 rounded-xl border border-ink/10 bg-white p-5 sm:grid-cols-4" noValidate>
        <div>
          <label htmlFor="f-status" className="text-xs font-medium text-ink/60">Status</label>
          <select id="f-status" value={draft.status} onChange={update("status")} className={input}>
            <option value="">Any</option>
            <option value="SUCCESS">Success</option>
            <option value="FAILED">Failed</option>
            <option value="PENDING">Pending</option>
          </select>
        </div>
        <div>
          <label htmlFor="f-category" className="text-xs font-medium text-ink/60">Category</label>
          <select id="f-category" value={draft.category} onChange={update("category")} className={input}>
            <option value="">Any</option>
            {CATEGORIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="f-card" className="text-xs font-medium text-ink/60">Card number</label>
          <input id="f-card" value={draft.card} onChange={update("card")} maxLength={25} placeholder="**** 4242" autoComplete="off" className={`amount ${input}`} />
        </div>
        {seesAll ? (
          <div>
            <label htmlFor="f-fraud" className="text-xs font-medium text-ink/60">Fraud status</label>
            <select id="f-fraud" value={draft.fraud_status} onChange={update("fraud_status")} className={input}>
              <option value="">Any</option>
              <option value="FLAGGED">Flagged</option>
              <option value="CONFIRMED">Confirmed fraud</option>
              <option value="CLEARED">Cleared</option>
              <option value="CLEAN">Clean</option>
            </select>
          </div>
        ) : <div className="hidden sm:block" />}
        <div>
          <label htmlFor="f-from" className="text-xs font-medium text-ink/60">From</label>
          <input id="f-from" type="date" value={draft.date_from} onChange={update("date_from")} className={input} />
        </div>
        <div>
          <label htmlFor="f-to" className="text-xs font-medium text-ink/60">To</label>
          <input id="f-to" type="date" value={draft.date_to} onChange={update("date_to")} className={input} />
        </div>
        <div>
          <label htmlFor="f-min" className="text-xs font-medium text-ink/60">Min amount</label>
          <input id="f-min" type="number" min="0" step="0.01" value={draft.min_amount} onChange={update("min_amount")} className={input} />
        </div>
        <div>
          <label htmlFor="f-max" className="text-xs font-medium text-ink/60">Max amount</label>
          <input id="f-max" type="number" min="0" step="0.01" value={draft.max_amount} onChange={update("max_amount")} className={input} />
        </div>
        {formError && <p role="alert" className="col-span-2 text-sm text-danger sm:col-span-4">{formError}</p>}
        <div className="col-span-2 flex items-end gap-2 sm:col-span-4">
          <button type="submit" className="rounded-md bg-ledger-500 px-4 py-1.5 text-sm font-medium text-white hover:bg-ledger-600">Apply filters</button>
          <button type="button" onClick={clearFilters} className="rounded-md border border-ink/15 px-4 py-1.5 text-sm font-medium text-ink/70 hover:bg-ink/5">Clear</button>
        </div>
      </form>

      {error && <p role="alert" className="mt-4 text-sm text-danger">{error}</p>}

      <div className="mt-6 overflow-x-auto rounded-xl border border-ink/10 bg-white" aria-busy={loading}>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ink/10 text-left text-xs text-ink/50">
              <SortHeader label="Date" field="created_at" ordering={ordering} onSort={sortBy} />
              {seesAll && <th scope="col" className="px-4 py-3 uppercase tracking-wide">User</th>}
              <th scope="col" className="px-4 py-3 uppercase tracking-wide">Card</th>
              <SortHeader label="Amount" field="amount" ordering={ordering} onSort={sortBy} />
              <SortHeader label="Status" field="status" ordering={ordering} onSort={sortBy} />
              {seesAll && <th scope="col" className="px-4 py-3 uppercase tracking-wide">Fraud</th>}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={columns} className="px-4 py-8 text-center text-ink/50">Loading...</td></tr>
            ) : data.results.length === 0 ? (
              <tr><td colSpan={columns} className="px-4 py-8 text-center text-ink/50">No transactions match these filters.</td></tr>
            ) : (
              data.results.map((t) => (
                <tr key={t.id} className="border-b border-ink/5 last:border-0">
                  <td className="px-4 py-3 text-ink/70">{new Date(t.created_at).toLocaleString()}</td>
                  {seesAll && <td className="px-4 py-3 text-ink/70">{t.user_email}</td>}
                  <td className="px-4 py-3 text-ink/70">{t.card_brand ? `${t.card_brand} •••• ${t.card_last4}` : "—"}</td>
                  <td className="amount px-4 py-3 text-ink">{t.currency} {t.amount}</td>
                  <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                  {seesAll && (
                    <td className="px-4 py-3">
                      {t.fraud_status && t.fraud_status !== "CLEAN" ? (
                        <span className="inline-flex rounded-full border border-red-200 bg-red-50 px-2.5 py-0.5 text-xs font-semibold text-danger">{t.fraud_status}</span>
                      ) : <span className="text-ink/40">—</span>}
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Pagination
        page={page}
        pageSize={pageSize}
        count={data.count}
        onPage={setPage}
        onPageSize={(n) => { setPageSize(n); setPage(1); }}
      />
    </div>
  );
}