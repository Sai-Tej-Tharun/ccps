// Server-side pagination controls: the parent owns page / pageSize and re-fetches on change.
export default function Pagination({ page, pageSize, count, onPage, onPageSize, sizes = [10, 20, 50, 100] }) {
  const pages = Math.max(1, Math.ceil(count / pageSize));
  const from = count === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, count);

  const btn =
    "rounded-md border border-ink/15 px-3 py-1.5 text-sm font-medium text-ink/70 hover:bg-ink/5 disabled:cursor-not-allowed disabled:opacity-40";

  return (
    <nav aria-label="Pagination" className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm">
      <p className="text-ink/60" aria-live="polite">
        {count === 0 ? "No results" : `Showing ${from}-${to} of ${count}`}
      </p>
      <div className="flex items-center gap-3">
        {onPageSize && (
          <label className="flex items-center gap-2 text-ink/60">
            Rows
            <select
              value={pageSize}
              onChange={(e) => onPageSize(Number(e.target.value))}
              className="rounded-md border border-ink/15 px-2 py-1 text-sm"
            >
              {sizes.map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </label>
        )}
        <button type="button" className={btn} disabled={page <= 1} onClick={() => onPage(page - 1)}>
          Previous
        </button>
        <span className="text-ink/70">Page {page} of {pages}</span>
        <button type="button" className={btn} disabled={page >= pages} onClick={() => onPage(page + 1)}>
          Next
        </button>
      </div>
    </nav>
  );
}