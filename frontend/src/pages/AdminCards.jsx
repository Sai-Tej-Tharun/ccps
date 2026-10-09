import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  blockCard,
  fetchAdminCards,
  fetchCardActivity,
  unblockCard,
  updateCardCreditLimit,
} from "../api/admin";
import { extractErrorMessage } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";

const PAGE_SIZE = 20; // matches REST_FRAMEWORK["PAGE_SIZE"] in Django settings
const MAX_LIMIT = 10000000;

const amount = (value) =>
  Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const when = (iso) =>
  iso ? new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }) : "—";

function useDebounced(value, delay = 350) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

function CardStatus({ blocked }) {
  const style = blocked
    ? "bg-red-50 text-danger border-red-200"
    : "bg-ledger-50 text-ledger-700 border-ledger-300";
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${style}`}>
      {blocked ? "Blocked" : "Active"}
    </span>
  );
}

// Accessible modal: labelled, Escape closes, focus is trapped and restored.
function Modal({ title, onClose, children }) {
  const dialogRef = useRef(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  useEffect(() => {
    const previouslyFocused = document.activeElement;
    dialogRef.current?.focus();

    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        closeRef.current();
        return;
      }
      if (event.key !== "Tab" || !dialogRef.current) return;
      const focusable = dialogRef.current.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previouslyFocused?.focus?.();
    };
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        tabIndex={-1}
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-ink/10 bg-white p-6 shadow-xl outline-none"
      >
        <div className="flex items-start justify-between gap-4">
          <h2 id="modal-title" className="font-serif text-lg text-ink">{title}</h2>
          <button type="button" onClick={onClose} aria-label="Close dialog" className="rounded-md px-2 py-1 text-ink/60 hover:bg-ink/5">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function CreditLimitModal({ card, onClose, onSaved }) {
  const [value, setValue] = useState(String(card.credit_limit));
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    const trimmed = value.trim();
    const n = Number(trimmed);
    if (!/^\d+(\.\d{1,2})?$/.test(trimmed) || n < 1 || n > MAX_LIMIT) {
      setError(`Enter an amount between 1.00 and ${amount(MAX_LIMIT)} with at most 2 decimal places.`);
      return;
    }
    setSaving(true);
    setError("");
    try {
      onSaved(await updateCardCreditLimit(card.id, trimmed));
    } catch (err) {
      setError(extractErrorMessage(err, "Could not update the credit limit."));
      setSaving(false);
    }
  };

  return (
    <Modal title="Update credit limit" onClose={onClose}>
      <p className="mt-1 text-sm text-ink/60">
        {card.brand} {card.masked_number} · {card.owner_email}
      </p>
      <form onSubmit={submit} className="mt-5 space-y-4" noValidate>
        <div>
          <label htmlFor="credit-limit" className="text-sm font-medium text-ink/80">New credit limit</label>
          <input
            id="credit-limit"
            inputMode="decimal"
            autoComplete="off"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? "credit-limit-error" : undefined}
            className="amount mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
          />
          <p className="mt-1 text-xs text-ink/50">Current limit: {amount(card.credit_limit)}</p>
        </div>
        {error && <p id="credit-limit-error" role="alert" className="text-sm text-danger">{error}</p>}
        <div className="flex justify-end gap-3">
          <button type="button" onClick={onClose} className="rounded-md border border-ink/15 px-4 py-2 text-sm font-medium text-ink/70 hover:bg-ink/5">
            Cancel
          </button>
          <button type="submit" disabled={saving} className="rounded-md bg-ledger-500 px-4 py-2 text-sm font-medium text-white hover:bg-ledger-600 disabled:opacity-60">
            {saving ? "Saving..." : "Save limit"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ActivityModal({ card, onClose }) {
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ results: [], count: 0, next: null, previous: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    fetchCardActivity(card.id, page)
      .then((d) => !cancelled && setData(d))
      .catch((err) => !cancelled && setError(extractErrorMessage(err, "Could not load card activity.")))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [card.id, page]);

  return (
    <Modal title="Card activity" onClose={onClose}>
      <p className="mt-1 text-sm text-ink/60">
        {card.brand} {card.masked_number} · {card.owner_email}
      </p>
      <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
        <div className="rounded-lg border border-ink/10 p-3">
          <p className="text-xs uppercase tracking-wide text-ink/50">Transactions</p>
          <p className="mt-1 font-semibold text-ink">{card.transaction_count}</p>
        </div>
        <div className="rounded-lg border border-ink/10 p-3">
          <p className="text-xs uppercase tracking-wide text-ink/50">Total spent</p>
          <p className="amount mt-1 font-semibold text-ink">{amount(card.total_spent)}</p>
        </div>
        <div className="rounded-lg border border-ink/10 p-3">
          <p className="text-xs uppercase tracking-wide text-ink/50">Last activity</p>
          <p className="mt-1 font-semibold text-ink">{when(card.last_activity)}</p>
        </div>
      </div>

      {error && <p role="alert" className="mt-4 text-sm text-danger">{error}</p>}

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ink/10 text-left text-xs uppercase tracking-wide text-ink/50">
              <th scope="col" className="py-2 pr-3">Date</th>
              <th scope="col" className="py-2 pr-3">Reference</th>
              <th scope="col" className="py-2 pr-3">Amount</th>
              <th scope="col" className="py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} className="py-6 text-center text-ink/50">Loading...</td></tr>
            ) : data.results.length === 0 ? (
              <tr><td colSpan={4} className="py-6 text-center text-ink/50">No activity on this card yet.</td></tr>
            ) : (
              data.results.map((t) => (
                <tr key={t.id} className="border-b border-ink/5 last:border-0">
                  <td className="py-2 pr-3 text-ink/70">{when(t.created_at)}</td>
                  <td className="py-2 pr-3 font-mono text-xs text-ink/70">{t.reference.slice(0, 12)}</td>
                  <td className="amount py-2 pr-3 text-ink">{t.currency} {amount(t.amount)}</td>
                  <td className="py-2">
                    <StatusBadge status={t.status} />
                    {t.failure_reason && <p className="mt-1 text-xs text-ink/50">{t.failure_reason}</p>}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm">
        <button
          type="button"
          disabled={!data.previous || loading}
          onClick={() => setPage((p) => p - 1)}
          className="rounded-md border border-ink/15 px-3 py-1.5 font-medium text-ink/70 hover:bg-ink/5 disabled:opacity-40"
        >
          ← Previous
        </button>
        <span className="text-ink/60">Page {page} of {Math.max(1, Math.ceil(data.count / PAGE_SIZE))}</span>
        <button
          type="button"
          disabled={!data.next || loading}
          onClick={() => setPage((p) => p + 1)}
          className="rounded-md border border-ink/15 px-3 py-1.5 font-medium text-ink/70 hover:bg-ink/5 disabled:opacity-40"
        >
          Next →
        </button>
      </div>
    </Modal>
  );
}

export default function AdminCards() {
  const { can } = useAuth(); // buttons the role may not use are hidden; the server enforces it anyway
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ results: [], count: 0, next: null, previous: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [limitCard, setLimitCard] = useState(null);
  const [activityCard, setActivityCard] = useState(null);

  const debouncedSearch = useDebounced(search);
  const latestRequest = useRef(0);

  const load = useCallback(() => {
    const requestId = ++latestRequest.current;
    const isCurrent = () => requestId === latestRequest.current; // ignore out-of-order responses
    const params = { page };
    if (debouncedSearch.trim()) params.search = debouncedSearch.trim();
    if (statusFilter) params.status = statusFilter;

    setLoading(true);
    setError("");
    fetchAdminCards(params)
      .then((d) => isCurrent() && setData(d))
      .catch((err) => {
        if (!isCurrent()) return;
        if (err?.response?.status === 404 && page > 1) {
          setPage((p) => Math.max(1, p - 1)); // the last page emptied out
          return;
        }
        setError(extractErrorMessage(err, "Could not load cards."));
      })
      .finally(() => isCurrent() && setLoading(false));
  }, [page, debouncedSearch, statusFilter]);

  useEffect(load, [load]);

  const replaceCard = (updated) =>
    setData((d) => ({ ...d, results: d.results.map((c) => (c.id === updated.id ? updated : c)) }));

  const toggleBlock = async (card) => {
    const blocking = !card.is_blocked;
    const verb = blocking ? "block" : "unblock";
    const confirmed = window.confirm(
      `Are you sure you want to ${verb} the ${card.brand} card ending ${card.last4} (${card.owner_email})?` +
        (blocking ? "\n\nThe owner will be e-mailed and the card will be declined for payments." : "")
    );
    if (!confirmed) return;

    setBusyId(card.id);
    setNotice("");
    setError("");
    try {
      const updated = blocking ? await blockCard(card.id) : await unblockCard(card.id);
      replaceCard(updated);
      setNotice(`Card ending ${card.last4} was ${blocking ? "blocked" : "unblocked"}.`);
    } catch (err) {
      setError(extractErrorMessage(err, `Could not ${verb} this card.`));
    } finally {
      setBusyId(null);
    }
  };

  const totalPages = Math.max(1, Math.ceil(data.count / PAGE_SIZE));
  const actionBtn = "rounded-md border border-ink/15 px-2.5 py-1 text-xs font-medium text-ink/80 hover:bg-ink/5 disabled:opacity-50";
  const dangerBtn = "rounded-md border border-red-200 px-2.5 py-1 text-xs font-medium text-danger hover:bg-ink/5 disabled:opacity-50";

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-ink">Card Management</h1>
        <Link to="/admin" className="text-sm font-medium text-ledger-600 hover:underline">← Admin dashboard</Link>
      </div>

      <div className="mt-6 flex flex-wrap items-end gap-3 rounded-xl border border-ink/10 bg-white p-5">
        <div className="min-w-[14rem] flex-1">
          <label htmlFor="card-search" className="text-xs font-medium text-ink/60">Search</label>
          <input
            id="card-search"
            type="search"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            maxLength={100}
            placeholder="Owner email, cardholder or last 4 digits"
            className="mt-1 w-full rounded-md border border-ink/15 px-3 py-1.5 text-sm outline-none focus:border-ledger-500"
          />
        </div>
        <div>
          <label htmlFor="card-status" className="text-xs font-medium text-ink/60">Status</label>
          <select
            id="card-status"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="mt-1 rounded-md border border-ink/15 px-3 py-1.5 text-sm outline-none focus:border-ledger-500"
          >
            <option value="">All cards</option>
            <option value="active">Active</option>
            <option value="blocked">Blocked</option>
          </select>
        </div>
      </div>

      <div aria-live="polite">
        {notice && <p className="mt-4 rounded-md border border-ledger-300 bg-ledger-50 px-4 py-2 text-sm text-ledger-700">{notice}</p>}
      </div>
      {error && <p role="alert" className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-danger">{error}</p>}

      <div className="mt-6 overflow-x-auto rounded-xl border border-ink/10 bg-white">
        <table className="w-full text-sm">
          <caption className="sr-only">All cards with owner, limit, spending and status</caption>
          <thead>
            <tr className="border-b border-ink/10 text-left text-xs uppercase tracking-wide text-ink/50">
              <th scope="col" className="px-4 py-3">Owner</th>
              <th scope="col" className="px-4 py-3">Card</th>
              <th scope="col" className="px-4 py-3">Expiry</th>
              <th scope="col" className="px-4 py-3 text-right">Limit</th>
              <th scope="col" className="px-4 py-3 text-right">Spent</th>
              <th scope="col" className="px-4 py-3 text-right">Txns</th>
              <th scope="col" className="px-4 py-3">Last activity</th>
              <th scope="col" className="px-4 py-3">Status</th>
              <th scope="col" className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && data.results.length === 0 ? (
              <tr><td colSpan={9} className="px-4 py-8 text-center text-ink/50">Loading...</td></tr>
            ) : data.results.length === 0 ? (
              <tr><td colSpan={9} className="px-4 py-8 text-center text-ink/50">No cards match these filters.</td></tr>
            ) : (
              data.results.map((card) => (
                <tr key={card.id} className="border-b border-ink/5 align-top last:border-0">
                  <td className="px-4 py-3">
                    <p className="text-ink">{card.owner_name || "—"}</p>
                    <p className="text-xs text-ink/60">{card.owner_email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <p className="amount whitespace-nowrap text-ink">{card.masked_number}</p>
                    <p className="text-xs text-ink/60">{card.brand} · {card.cardholder_name}</p>
                  </td>
                  <td className="amount px-4 py-3 text-ink/70">
                    {String(card.expiry_month).padStart(2, "0")}/{card.expiry_year}
                  </td>
                  <td className="amount px-4 py-3 text-right text-ink">{amount(card.credit_limit)}</td>
                  <td className="amount px-4 py-3 text-right text-ink/70">{amount(card.total_spent)}</td>
                  <td className="px-4 py-3 text-right text-ink/70">{card.transaction_count}</td>
                  <td className="px-4 py-3 text-ink/70">{when(card.last_activity)}</td>
                  <td className="px-4 py-3"><CardStatus blocked={card.is_blocked} /></td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-2">
                      {can("cards.block") && (
                        <button
                          type="button"
                          onClick={() => toggleBlock(card)}
                          disabled={busyId === card.id}
                          aria-label={`${card.is_blocked ? "Unblock" : "Block"} card ending ${card.last4}`}
                          className={card.is_blocked ? actionBtn : dangerBtn}
                        >
                          {busyId === card.id ? "Working..." : card.is_blocked ? "Unblock" : "Block"}
                        </button>
                      )}
                      {can("cards.update_limit") && (
                        <button type="button" onClick={() => setLimitCard(card)} aria-label={`Edit credit limit for card ending ${card.last4}`} className={actionBtn}>
                          Edit limit
                        </button>
                      )}
                      <button type="button" onClick={() => setActivityCard(card)} aria-label={`View activity for card ending ${card.last4}`} className={actionBtn}>
                        Activity
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm">
        <button
          type="button"
          disabled={!data.previous || loading}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="rounded-md border border-ink/15 px-3 py-1.5 font-medium text-ink/70 hover:bg-ink/5 disabled:opacity-40"
        >
          ← Previous
        </button>
        <span className="text-ink/60">
          Page {page} of {totalPages} · {data.count} card{data.count === 1 ? "" : "s"}
        </span>
        <button
          type="button"
          disabled={!data.next || loading}
          onClick={() => setPage((p) => p + 1)}
          className="rounded-md border border-ink/15 px-3 py-1.5 font-medium text-ink/70 hover:bg-ink/5 disabled:opacity-40"
        >
          Next →
        </button>
      </div>

      {limitCard && (
        <CreditLimitModal
          card={limitCard}
          onClose={() => setLimitCard(null)}
          onSaved={(updated) => {
            replaceCard(updated);
            setNotice(`Credit limit for card ending ${updated.last4} is now ${amount(updated.credit_limit)}.`);
            setLimitCard(null);
          }}
        />
      )}
      {activityCard && <ActivityModal card={activityCard} onClose={() => setActivityCard(null)} />}
    </div>
      );
}