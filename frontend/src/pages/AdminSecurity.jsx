import { useCallback, useEffect, useState } from "react";
import {
  fetchAuditLogs,
  fetchFraudLogs,
  fetchRoleMatrix,
  fetchStaffUsers,
  reviewFraudLog,
  setUserRole,
} from "../api/admin";
import { extractErrorMessage } from "../api/client";
import Pagination from "../components/Pagination";
import { useAuth } from "../context/AuthContext";

const PAGE_SIZE = 20; // matches REST_FRAMEWORK["PAGE_SIZE"] in Django settings
const when = (iso) => (iso ? new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }) : "—");
const ROLE_LABELS = { ADMIN: "Admin", SUPPORT: "Support", READ_ONLY: "Read-Only" };

function useDebounced(value, delay = 350) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

const select = "rounded-md border border-ink/15 px-2 py-1.5 text-sm";
const smallBtn = "rounded-md border border-ink/15 px-2.5 py-1 text-xs font-medium text-ink/70 hover:bg-ink/5 disabled:opacity-50";

// ------------------------------------------------------------------ Fraud alerts
function FraudTab({ canReview }) {
  const [reviewed, setReviewed] = useState("false");
  const [rule, setRule] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ count: 0, results: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(null); // the alert being reviewed
  const [resolution, setResolution] = useState("FALSE_POSITIVE");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    const params = { page };
    if (reviewed) params.reviewed = reviewed;
    if (rule) params.rule = rule;
    fetchFraudLogs(params)
      .then((d) => { setData(d); setError(""); })
      .catch((err) => setError(extractErrorMessage(err, "Could not load fraud alerts.")))
      .finally(() => setLoading(false));
  }, [reviewed, rule, page]);

  useEffect(load, [load]);

  const submitReview = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await reviewFraudLog(open.id, { resolution, note: note.trim() });
      setOpen(null);
      setNote("");
      load();
    } catch (err) {
      setError(extractErrorMessage(err, "Could not save the review."));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="flex flex-wrap gap-3">
        <label className="text-xs font-medium text-ink/60">Status
          <select value={reviewed} onChange={(e) => { setReviewed(e.target.value); setPage(1); }} className={`${select} mt-1 block`}>
            <option value="false">Needs review</option>
            <option value="true">Reviewed</option>
            <option value="">All</option>
          </select>
        </label>
        <label className="text-xs font-medium text-ink/60">Rule
          <select value={rule} onChange={(e) => { setRule(e.target.value); setPage(1); }} className={`${select} mt-1 block`}>
            <option value="">Any rule</option>
            <option value="HIGH_VALUE_BURST">High-value burst</option>
            <option value="MULTI_SOURCE">Different devices / locations</option>
          </select>
        </label>
      </div>
      {error && <p role="alert" className="mt-3 text-sm text-danger">{error}</p>}

      <div className="mt-4 overflow-x-auto rounded-xl border border-ink/10 bg-white" aria-busy={loading}>
        <table className="w-full text-sm">
          <caption className="sr-only">Transactions flagged by the fraud rules</caption>
          <thead>
            <tr className="border-b border-ink/10 text-left text-xs uppercase tracking-wide text-ink/50">
              <th scope="col" className="px-4 py-3">When</th>
              <th scope="col" className="px-4 py-3">Customer / card</th>
              <th scope="col" className="px-4 py-3">Rule</th>
              <th scope="col" className="px-4 py-3 text-right">Amount</th>
              <th scope="col" className="px-4 py-3">Outcome</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink/50">Loading...</td></tr>
            ) : data.results.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink/50">No fraud alerts here.</td></tr>
            ) : (
              data.results.map((log) => (
                <tr key={log.id} className="border-b border-ink/5 align-top last:border-0">
                  <td className="whitespace-nowrap px-4 py-3 text-ink/70">{when(log.created_at)}</td>
                  <td className="px-4 py-3">
                    <p className="text-ink">{log.user_email}</p>
                    <p className="amount text-xs text-ink/60">•••• {log.card_last4 ?? "—"} · {log.ip_address || "no IP"}</p>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-ink">{log.rule_label}</p>
                    <p className="text-xs text-ink/60">{log.details}</p>
                    <p className="text-xs text-ink/50">Severity: {log.severity}</p>
                  </td>
                  <td className="amount whitespace-nowrap px-4 py-3 text-right text-ink">{log.currency} {log.amount}</td>
                  <td className="px-4 py-3">
                    {log.reviewed ? (
                      <div className="text-xs text-ink/70">
                        <p className="font-semibold">{log.resolution === "CONFIRMED_FRAUD" ? "Confirmed fraud" : "False positive"}</p>
                        <p>{log.reviewed_by_email} · {when(log.reviewed_at)}</p>
                        {log.review_note && <p className="text-ink/50">{log.review_note}</p>}
                      </div>
                    ) : canReview ? (
                      <button type="button" className={smallBtn} onClick={() => { setOpen(log); setResolution("FALSE_POSITIVE"); setNote(""); }}>
                        Review
                      </button>
                    ) : <span className="text-xs text-ink/50">Awaiting review</span>}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageSize={PAGE_SIZE} count={data.count} onPage={setPage} />

      {open && (
        <form onSubmit={submitReview} aria-label="Review fraud alert" className="mt-6 rounded-xl border border-ink/10 bg-white p-5">
          <h3 className="font-serif text-base text-ink">Review alert for {open.user_email}</h3>
          <p className="mt-1 text-sm text-ink/60">{open.details}</p>
          <fieldset className="mt-4">
            <legend className="text-sm font-medium text-ink/80">Outcome</legend>
            <label className="mt-2 flex items-center gap-2 text-sm text-ink/80">
              <input type="radio" name="resolution" value="FALSE_POSITIVE" checked={resolution === "FALSE_POSITIVE"} onChange={(e) => setResolution(e.target.value)} />
              False positive (legitimate payment)
            </label>
            <label className="mt-1 flex items-center gap-2 text-sm text-ink/80">
              <input type="radio" name="resolution" value="CONFIRMED_FRAUD" checked={resolution === "CONFIRMED_FRAUD"} onChange={(e) => setResolution(e.target.value)} />
              Confirmed fraud
            </label>
          </fieldset>
          <label htmlFor="review-note" className="mt-4 block text-sm font-medium text-ink/80">Note (optional)</label>
          <textarea id="review-note" value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} rows={2} className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 text-sm" />
          <div className="mt-4 flex gap-3">
            <button type="submit" disabled={saving} className="rounded-md bg-ledger-500 px-4 py-2 text-sm font-medium text-white hover:bg-ledger-600 disabled:opacity-60">
              {saving ? "Saving..." : "Save review"}
            </button>
            <button type="button" onClick={() => setOpen(null)} className="rounded-md border border-ink/15 px-4 py-2 text-sm font-medium text-ink/70 hover:bg-ink/5">Cancel</button>
          </div>
        </form>
      )}
    </div>
  );
}

// ------------------------------------------------------------------ Audit log
function describeChanges(changes) {
  const entries = Object.entries(changes || {});
  if (entries.length === 0) return "—";
  return entries
    .map(([field, value]) =>
      value && typeof value === "object" && ("old" in value || "new" in value)
        ? `${field}: ${value.old ?? "none"} → ${value.new ?? "none"}`
        : `${field}: ${typeof value === "object" ? JSON.stringify(value) : value}`
    )
    .join("; ");
}

function AuditTab() {
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ count: 0, results: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const debounced = useDebounced(action);

  useEffect(() => { setPage(1); }, [debounced]);
  useEffect(() => {
    setLoading(true);
    fetchAuditLogs({ page, ...(debounced ? { action: debounced } : {}) })
      .then((d) => { setData(d); setError(""); })
      .catch((err) => setError(extractErrorMessage(err, "Could not load the audit log.")))
      .finally(() => setLoading(false));
  }, [page, debounced]);

  return (
    <div>
      <label htmlFor="audit-search" className="text-xs font-medium text-ink/60">Search by action</label>
      <input id="audit-search" value={action} onChange={(e) => setAction(e.target.value)} placeholder="e.g. credit limit" className={`${select} mt-1 block w-full sm:w-72`} />
      {error && <p role="alert" className="mt-3 text-sm text-danger">{error}</p>}
      <div className="mt-4 overflow-x-auto rounded-xl border border-ink/10 bg-white" aria-busy={loading}>
        <table className="w-full text-sm">
          <caption className="sr-only">Audit trail of administrator actions</caption>
          <thead>
            <tr className="border-b border-ink/10 text-left text-xs uppercase tracking-wide text-ink/50">
              <th scope="col" className="px-4 py-3">When</th>
              <th scope="col" className="px-4 py-3">Who</th>
              <th scope="col" className="px-4 py-3">Action</th>
              <th scope="col" className="px-4 py-3">Changes</th>
              <th scope="col" className="px-4 py-3">IP</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink/50">Loading...</td></tr>
            ) : data.results.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink/50">No audit entries.</td></tr>
            ) : (
              data.results.map((row) => (
                <tr key={row.id} className="border-b border-ink/5 align-top last:border-0">
                  <td className="whitespace-nowrap px-4 py-3 text-ink/70">{when(row.created_at)}</td>
                  <td className="px-4 py-3"><p className="text-ink">{row.admin_email}</p><p className="text-xs text-ink/50">{ROLE_LABELS[row.role] || row.role || "—"}</p></td>
                  <td className="px-4 py-3"><p className="text-ink">{row.action}</p>{row.target_type && <p className="text-xs text-ink/50">{row.target_type} #{row.target_id || "—"}</p>}</td>
                  <td className="px-4 py-3 text-xs text-ink/70">{describeChanges(row.changes)}</td>
                  <td className="amount px-4 py-3 text-xs text-ink/60">{row.ip_address || "—"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageSize={PAGE_SIZE} count={data.count} onPage={setPage} />
    </div>
  );
}

// ------------------------------------------------------------------ Roles
function RolesTab() {
  const { user: me } = useAuth();
  const [matrix, setMatrix] = useState(null);
  const [search, setSearch] = useState("");
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyId, setBusyId] = useState(null);
  const debounced = useDebounced(search.trim());

  useEffect(() => {
    fetchRoleMatrix().then(setMatrix).catch((err) => setError(extractErrorMessage(err, "Could not load roles.")));
  }, []);

  useEffect(() => {
    // Empty box = people who already have a role. 3+ characters = search every user (to promote a customer).
    if (debounced && debounced.length < 3) return;
    fetchStaffUsers(debounced ? { search: debounced, all: "true" } : {})
      .then((d) => setUsers(d.results ?? d))
      .catch((err) => setError(extractErrorMessage(err, "Could not load users.")));
  }, [debounced]);

  const change = async (target, role) => {
    setBusyId(target.id);
    setError("");
    setNotice("");
    try {
      const updated = await setUserRole(target.id, role);
      setUsers((list) => list.map((u) => (u.id === updated.id ? updated : u)));
      setNotice(`${updated.email} is now ${updated.role ? ROLE_LABELS[updated.role] : "a regular customer"}.`);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not change the role."));
    } finally {
      setBusyId(null);
    }
  };

  const allPerms = matrix ? [...new Set(Object.values(matrix).flat())].sort() : [];

  return (
    <div>
      {matrix && (
        <div className="overflow-x-auto rounded-xl border border-ink/10 bg-white">
          <table className="w-full text-sm">
            <caption className="sr-only">Permissions granted to each role</caption>
            <thead>
              <tr className="border-b border-ink/10 text-left text-xs uppercase tracking-wide text-ink/50">
                <th scope="col" className="px-4 py-3">Permission</th>
                {Object.keys(matrix).map((role) => <th key={role} scope="col" className="px-4 py-3 text-center">{ROLE_LABELS[role]}</th>)}
              </tr>
            </thead>
            <tbody>
              {allPerms.map((perm) => (
                <tr key={perm} className="border-b border-ink/5 last:border-0">
                  <th scope="row" className="amount px-4 py-2 text-left text-xs font-normal text-ink/80">{perm}</th>
                  {Object.keys(matrix).map((role) => (
                    <td key={role} className="px-4 py-2 text-center">
                      {matrix[role].includes(perm) ? <span aria-label="Allowed" className="text-ledger-600">✓</span> : <span aria-label="Not allowed" className="text-ink/30">—</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h3 className="mt-8 font-serif text-base text-ink">Assign roles</h3>
      <label htmlFor="user-search" className="mt-2 block text-xs font-medium text-ink/60">Find a user (3+ characters), or leave empty to list staff</label>
      <input id="user-search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="name or e-mail" className={`${select} mt-1 block w-full sm:w-72`} />
      {error && <p role="alert" className="mt-3 text-sm text-danger">{error}</p>}
      {notice && <p role="status" className="mt-3 text-sm text-ledger-600">{notice}</p>}

      <div className="mt-4 overflow-x-auto rounded-xl border border-ink/10 bg-white">
        <table className="w-full text-sm">
          <caption className="sr-only">Users and their roles</caption>
          <thead>
            <tr className="border-b border-ink/10 text-left text-xs uppercase tracking-wide text-ink/50">
              <th scope="col" className="px-4 py-3">User</th>
              <th scope="col" className="px-4 py-3">Role</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr><td colSpan={2} className="px-4 py-6 text-center text-ink/50">No users to show.</td></tr>
            ) : (
              users.map((u) => (
                <tr key={u.id} className="border-b border-ink/5 last:border-0">
                  <td className="px-4 py-3 text-ink">{u.email}</td>
                  <td className="px-4 py-3">
                    <select
                      aria-label={`Role for ${u.email}`}
                      value={u.role ?? "NONE"}
                      disabled={busyId === u.id || u.id === me?.id}
                      title={u.id === me?.id ? "You cannot change your own role" : undefined}
                      onChange={(e) => change(u, e.target.value)}
                      className={select}
                    >
                      <option value="NONE">Customer (no role)</option>
                      <option value="READ_ONLY">Read-Only</option>
                      <option value="SUPPORT">Support</option>
                      <option value="ADMIN">Admin</option>
                    </select>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ Page
export default function AdminSecurity() {
  const { can } = useAuth();
  const tabs = [
    can("fraud.view") && { id: "fraud", label: "Fraud alerts" },
    can("audit.view") && { id: "audit", label: "Audit log" },
    can("roles.manage") && { id: "roles", label: "Roles" },
  ].filter(Boolean);
  const [active, setActive] = useState(tabs[0]?.id);

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-semibold text-ink">Security</h1>
      <div role="tablist" aria-label="Security sections" className="mt-6 flex gap-2 border-b border-ink/10">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={active === tab.id}
            aria-controls={`panel-${tab.id}`}
            onClick={() => setActive(tab.id)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${
              active === tab.id ? "border-ledger-500 text-ledger-600" : "border-transparent text-ink/60 hover:text-ink"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" id={`panel-${active}`} aria-labelledby={`tab-${active}`} className="mt-6">
        {active === "fraud" && <FraudTab canReview={can("fraud.review")} />}
        {active === "audit" && <AuditTab />}
        {active === "roles" && <RolesTab />}
      </div>
    </div>
  );
}