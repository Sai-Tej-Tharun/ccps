import { useState } from "react";
import { downloadMonthlyStatement } from "../api/transactions";

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

// A failed blob download still carries a JSON error body - read it as text.
async function readError(error) {
  const data = error?.response?.data;
  if (data instanceof Blob) {
    try {
      const body = JSON.parse(await data.text());
      if (typeof body.detail === "string") return body.detail;
      const first = Object.values(body)[0];
      if (Array.isArray(first)) return String(first[0]);
    } catch {
      /* fall through */
    }
  }
  return "Could not generate the statement. Please try again.";
}

export default function StatementDownload() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const years = Array.from({ length: 6 }, (_, i) => now.getFullYear() - i);
  const isFuture = year === now.getFullYear() && month > now.getMonth() + 1;

  const handleDownload = async () => {
    if (isFuture) {
      setError("Choose a month that has already started.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await downloadMonthlyStatement({ year, month });
    } catch (err) {
      setError(await readError(err));
    } finally {
      setBusy(false);
    }
  };

  const selectClass =
    "mt-1 rounded-md border border-ink/15 px-2 py-1.5 text-sm outline-none focus:border-ledger-500";

  return (
    <section aria-labelledby="statement-heading" className="mt-8 rounded-xl border border-ink/10 bg-white p-6">
      <h2 id="statement-heading" className="font-serif text-lg text-ink">Monthly statement</h2>
      <p className="mt-1 text-sm text-ink/60">
        Download a PDF of your transactions, total spending and summary for any month.
      </p>

      <div className="mt-4 flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="statement-month" className="block text-xs font-medium text-ink/60">Month</label>
          <select id="statement-month" value={month} onChange={(e) => setMonth(Number(e.target.value))} className={selectClass}>
            {MONTH_NAMES.map((name, i) => (
              <option key={name} value={i + 1}>{name}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="statement-year" className="block text-xs font-medium text-ink/60">Year</label>
          <select id="statement-year" value={year} onChange={(e) => setYear(Number(e.target.value))} className={selectClass}>
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
        <button
          type="button"
          onClick={handleDownload}
          disabled={busy}
          className="rounded-md bg-ledger-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-ledger-600 disabled:opacity-60"
        >
          {busy ? "Preparing..." : "Download PDF"}
        </button>
      </div>

      {error && <p role="alert" className="mt-3 text-sm text-danger">{error}</p>}
    </section>
  );
}