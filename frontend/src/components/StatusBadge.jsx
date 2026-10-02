const STYLES = {
  SUCCESS: "bg-ledger-50 text-ledger-700 border-ledger-300",
  FAILED: "bg-red-50 text-danger border-red-200",
  PENDING: "bg-amber-50 text-warn border-amber-200",
};

export default function StatusBadge({ status }) {
  const style = STYLES[status] || "bg-ink/5 text-ink/70 border-ink/10";
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${style}`}>
      {status}
    </span>
  );
}
