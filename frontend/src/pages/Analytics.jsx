import { useEffect, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  downloadAnalyticsExport,
  fetchCategoryBreakdown,
  fetchMonthlySummary,
  fetchUtilization,
} from "../api/analytics";
import { extractErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

// Colours chosen to stay readable on both the light and the dark surface.
const COLORS = ["#2E8B73", "#D9822B", "#4C8DD6", "#A56ACF", "#D95C54", "#8DAA3F", "#8A94A6"];
const CURRENCY = "USD";

const money = (value) =>
  Number(value || 0).toLocaleString(undefined, { style: "currency", currency: CURRENCY });

const tooltipStyle = {
  background: "rgb(var(--color-surface))",
  border: "1px solid rgb(var(--color-ink) / 0.15)",
  borderRadius: 8,
  color: "rgb(var(--color-ink))",
};

function ChartCard({ title, description, children, table }) {
  return (
    <section className="rounded-xl border border-ink/10 bg-white p-5" aria-label={title}>
      <h2 className="font-serif text-lg text-ink">{title}</h2>
      <p className="mt-1 text-xs text-ink/50">{description}</p>
      <div className="mt-4 h-72 text-ink/60">{children}</div>
      {table}
    </section>
  );
}

// Screen-reader version of a chart's numbers.
function SrTable({ caption, head, rows }) {
  return (
    <div className="sr-only"> {/* a wrapper: sr-only on a <table> itself does not shrink it */}
      <table>
        <caption>{caption}</caption>
        <thead><tr>{head.map((h) => <th key={h} scope="col">{h}</th>)}</tr></thead>
        <tbody>{rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}

function Tile({ label, value }) {
  return (
    <div className="rounded-xl border border-ink/10 bg-white p-5">
      <p className="text-xs uppercase tracking-wide text-ink/50">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

export default function Analytics() {
  const { can } = useAuth();
  const canSeeAll = can("analytics.view");
  const [months, setMonths] = useState(6);
  const [scope, setScope] = useState("own");
  const [monthly, setMonthly] = useState([]);
  const [categories, setCategories] = useState([]);
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState("");
  const latest = useRef(0);

  useEffect(() => {
    const requestId = ++latest.current;
    const params = { months, currency: CURRENCY, scope };
    setLoading(true);
    setError("");
    Promise.all([fetchMonthlySummary(params), fetchCategoryBreakdown(params), fetchUtilization(params)])
      .then(([m, c, u]) => {
        if (requestId !== latest.current) return; // a newer request replaced this one
        setMonthly(m);
        setCategories(c);
        setUsage(u);
      })
      .catch((err) => requestId === latest.current && setError(extractErrorMessage(err, "Could not load analytics.")))
      .finally(() => requestId === latest.current && setLoading(false));
  }, [months, scope]);

  const handleExport = async (type) => {
    setExporting(type);
    setError("");
    try {
      await downloadAnalyticsExport({ months, currency: CURRENCY, scope }, type);
    } catch (err) {
      setError(extractErrorMessage(err, "Export failed."));
    } finally {
      setExporting("");
    }
  };

  const totalSpent = monthly.reduce((sum, m) => sum + Number(m.total_spent), 0);
  const totalCount = monthly.reduce((sum, m) => sum + m.success_count, 0);
  const lineData = monthly.map((m) => ({ ...m, total: Number(m.total_spent) }));
  const barData = (usage?.cards ?? []).map((c) => ({ ...c, utilization: c.utilization_percent }));
  const pieData = categories.map((c) => ({ ...c, value: Number(c.total) }));

  const control = "rounded-md border border-ink/15 px-2 py-1.5 text-sm";
  const exportBtn =
    "rounded-md border border-ledger-500 px-3 py-1.5 text-sm font-medium text-ledger-600 hover:bg-ledger-500 hover:text-white disabled:opacity-60";

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink">Analytics</h1>
          <p className="mt-1 text-sm text-ink/60">Spending, categories and credit utilization ({CURRENCY}).</p>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs font-medium text-ink/60">
            Period
            <select value={months} onChange={(e) => setMonths(Number(e.target.value))} className={`${control} mt-1 block`}>
              {[3, 6, 12, 24].map((n) => <option key={n} value={n}>Last {n} months</option>)}
            </select>
          </label>
          {canSeeAll && (
            <label className="text-xs font-medium text-ink/60">
              Data
              <select value={scope} onChange={(e) => setScope(e.target.value)} className={`${control} mt-1 block`}>
                <option value="own">My cards</option>
                <option value="all">All customers</option>
              </select>
            </label>
          )}
          <button type="button" className={exportBtn} disabled={Boolean(exporting)} onClick={() => handleExport("csv")}>
            {exporting === "csv" ? "Preparing..." : "Export CSV"}
          </button>
          <button type="button" className={exportBtn} disabled={Boolean(exporting)} onClick={() => handleExport("pdf")}>
            {exporting === "pdf" ? "Preparing..." : "Export PDF"}
          </button>
        </div>
      </div>

      {error && <p role="alert" className="mt-4 text-sm text-danger">{error}</p>}
      {loading && <p className="mt-6 text-sm text-ink/50" aria-live="polite">Loading analytics...</p>}

      {!loading && !error && (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <Tile label="Total spent" value={money(totalSpent)} />
            <Tile label="Successful payments" value={totalCount} />
            <Tile label="Credit utilization (this month)" value={`${usage?.utilization_percent ?? 0}%`} />
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <div className="lg:col-span-2">
              <ChartCard
                title="Monthly spending"
                description="Successful payments per month."
                table={<SrTable caption="Monthly spending" head={["Month", "Total spent", "Successful", "Failed"]} rows={monthly.map((m) => [m.label, m.total_spent, m.success_count, m.failed_count])} />}
              >
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={lineData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                    <CartesianGrid stroke="currentColor" strokeOpacity={0.12} vertical={false} />
                    <XAxis dataKey="label" tick={{ fill: "currentColor", fontSize: 12 }} stroke="currentColor" strokeOpacity={0.3} />
                    <YAxis tick={{ fill: "currentColor", fontSize: 12 }} stroke="currentColor" strokeOpacity={0.3} tickFormatter={(v) => Number(v).toLocaleString()} width={70} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v) => [money(v), "Spent"]} />
                    <Line type="monotone" dataKey="total" name="Spent" stroke={COLORS[0]} strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>

            <ChartCard
              title="Spending by category"
              description="Share of successful spending in the period."
              table={<SrTable caption="Spending by category" head={["Category", "Total", "Share"]} rows={categories.map((c) => [c.label, c.total, `${c.percent}%`])} />}
            >
              {pieData.length === 0 ? (
                <p className="pt-10 text-center text-sm text-ink/50">No spending in this period.</p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pieData} dataKey="value" nameKey="label" innerRadius={50} outerRadius={90} paddingAngle={2} stroke="rgb(var(--color-surface))">
                      {pieData.map((entry, i) => <Cell key={entry.category} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} formatter={(v, name, item) => [`${money(v)} (${item.payload.percent}%)`, name]} />
                    <Legend wrapperStyle={{ fontSize: 12 }} formatter={(value) => <span className="text-ink/70">{value}</span>} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </ChartCard>

            <ChartCard
              title="Credit utilization by card"
              description={`This month's spend as a percentage of each credit limit${usage && usage.card_count > 10 ? " (top 10 cards)" : ""}.`}
              table={<SrTable caption="Credit utilization by card" head={["Card", "Limit", "Spent", "Utilization"]} rows={(usage?.cards ?? []).map((c) => [c.label, c.credit_limit, c.spent, `${c.utilization_percent}%`])} />}
            >
              {barData.length === 0 ? (
                <p className="pt-10 text-center text-sm text-ink/50">No cards to show.</p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={barData} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
                    <CartesianGrid stroke="currentColor" strokeOpacity={0.12} horizontal={false} />
                    <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fill: "currentColor", fontSize: 12 }} stroke="currentColor" strokeOpacity={0.3} />
                    <YAxis type="category" dataKey="label" width={90} tick={{ fill: "currentColor", fontSize: 12 }} stroke="currentColor" strokeOpacity={0.3} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v}%`, "Utilization"]} />
                    <Bar dataKey="utilization" radius={[0, 4, 4, 0]}>
                      {barData.map((c) => (
                        <Cell key={c.card_id} fill={c.utilization_percent >= 90 ? COLORS[4] : c.utilization_percent >= 70 ? COLORS[1] : COLORS[0]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </ChartCard>
          </div>
        </>
      )}
    </div>
  );
}