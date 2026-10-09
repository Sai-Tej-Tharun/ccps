import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchSystemHealth } from "../api/admin";
import { extractErrorMessage } from "../api/client";

const REFRESH_MS = 30000;

function ServiceStatus({ name, info }) {
  const ok = info?.status === "ok";
  return (
    <div className="flex items-center justify-between rounded-lg border border-ink/10 px-4 py-3">
      <span className="text-sm text-ink/80">{name}</span>
      <span
        className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
          ok ? "border-ledger-300 bg-ledger-50 text-ledger-700" : "border-red-200 bg-red-50 text-danger"
        }`}
      >
        <span aria-hidden="true">{ok ? "●" : "▲"}</span>
        {ok ? `Operational${info.latency_ms != null ? ` · ${info.latency_ms} ms` : ""}` : "Down"}
      </span>
    </div>
  );
}

function Tile({ label, value, tone }) {
  return (
    <div className="rounded-xl border border-ink/10 bg-white p-4">
      <p className="text-xs uppercase tracking-wide text-ink/50">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${tone === "danger" ? "text-danger" : "text-ink"}`}>{value}</p>
    </div>
  );
}

export default function SystemHealthPanel() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    fetchSystemHealth(24)
      .then((data) => {
        setHealth(data);
        setError("");
      })
      .catch((err) => setError(extractErrorMessage(err, "Could not load system health.")))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, REFRESH_MS);
    return () => clearInterval(id); // stop polling when the panel unmounts
  }, [load]);

  const r = health?.requests;
  return (
    <section aria-labelledby="health-title" className="mt-8 rounded-xl border border-ink/10 bg-white p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="health-title" className="font-serif text-lg text-ink">System health (last 24 hours)</h2>
        <div className="flex items-center gap-3 text-xs text-ink/50">
          {health && <span aria-live="polite">Updated {new Date(health.checked_at).toLocaleTimeString()}</span>}
          <button type="button" onClick={load} disabled={loading} className="rounded-md border border-ink/15 px-2.5 py-1 text-ink/70 hover:bg-ink/5 disabled:opacity-50">
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {error && <p role="alert" className="mt-4 text-sm text-danger">{error}</p>}

      {health && (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <ServiceStatus name="Database" info={health.services.database} />
            <ServiceStatus name="Payment service (FastAPI)" info={health.services.payment_service} />
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Tile label="API requests" value={r.total} />
            <Tile label="Avg response" value={r.avg_ms == null ? "—" : `${r.avg_ms} ms`} />
            <Tile label="95th percentile" value={r.p95_ms == null ? "—" : `${r.p95_ms} ms`} />
            <Tile label="Server errors" value={`${r.server_errors} (${r.error_rate_percent}%)`} tone={r.server_errors > 0 ? "danger" : undefined} />
          </div>

          <div className="mt-4 flex flex-wrap gap-6 text-sm text-ink/70">
            <Link to="/admin/security" className="text-ledger-600 hover:underline">
              {health.open_fraud_alerts} open fraud alert{health.open_fraud_alerts === 1 ? "" : "s"}
            </Link>
            <Link to="/admin/cards" className="text-ledger-600 hover:underline">
              {health.blocked_cards} blocked card{health.blocked_cards === 1 ? "" : "s"}
            </Link>
          </div>

          <div className="mt-6 grid gap-6">
            <div className="overflow-x-auto">
              <h3 className="text-sm font-semibold text-ink">Slowest endpoints</h3>
              <table className="mt-2 w-full text-sm">
                <caption className="sr-only">Five slowest endpoints by average response time</caption>
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-ink/50">
                    <th scope="col" className="py-1 pr-3">Endpoint</th>
                    <th scope="col" className="py-1 pr-3 text-right">Avg</th>
                    <th scope="col" className="py-1 pr-3 text-right">Max</th>
                    <th scope="col" className="py-1 text-right">Calls</th>
                  </tr>
                </thead>
                <tbody>
                  {health.slowest_endpoints.length === 0 ? (
                    <tr><td colSpan={4} className="py-3 text-ink/50">No requests recorded yet.</td></tr>
                  ) : (
                    health.slowest_endpoints.map((e) => (
                      <tr key={`${e.service}${e.method}${e.path}`} className="border-t border-ink/5">
                        <td className="py-2 pr-3"><span className="amount text-xs text-ink/80">{e.method} {e.path}</span><span className="ml-2 text-xs text-ink/40">{e.service}</span></td>
                        <td className="amount whitespace-nowrap py-2 pr-3 text-right">{e.avg_ms} ms</td>
                        <td className="amount whitespace-nowrap py-2 pr-3 text-right">{e.max_ms} ms</td>
                        <td className="amount py-2 text-right">{e.requests}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-ink">Recent failures</h3>
              {health.recent_errors.length === 0 ? (
                <p className="mt-2 text-sm text-ink/50">No server errors in this period.</p>
              ) : (
                <ul className="mt-2 space-y-2 text-sm">
                  {health.recent_errors.map((e, i) => (
                    <li key={i} className="rounded-lg border border-red-200 bg-red-50 px-3 py-2">
                      <p className="amount text-xs text-danger">{e.status_code} · {e.method} {e.path} · {e.service}</p>
                      <p className="text-ink/70">{e.error || "No error message recorded"}</p>
                      <p className="text-xs text-ink/50">{new Date(e.created_at).toLocaleString()}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
}