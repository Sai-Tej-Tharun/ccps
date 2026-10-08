const BRAND_LABEL = {
  VISA: "Visa",
  MASTERCARD: "Mastercard",
  AMEX: "Amex",
  DISCOVER: "Discover",
  CARD: "Card",
};

export default function CardTile({ card, onDelete, selectable, selected, onSelect }) {
  return (
    <div
      onClick={() => selectable && !card.is_blocked && onSelect?.(card)}
      className={`rounded-xl border p-5 transition ${
        selectable && !card.is_blocked ? "cursor-pointer hover:border-ledger-400" : ""
      } ${selected ? "border-ledger-500 ring-2 ring-ledger-200" : "border-ink/10"} bg-white`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-ink/50">{BRAND_LABEL[card.brand] || card.brand}</p>
          <p className="amount mt-1 text-lg text-ink">{card.masked_number}</p>
          {card.is_blocked && (
            <span className="mt-2 inline-flex items-center rounded-full border border-red-200 bg-red-50 px-2.5 py-0.5 text-xs font-semibold text-danger">
              Blocked
            </span>
          )}
        </div>
        {onDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(card.id);
            }}
            className="text-xs font-medium text-danger hover:underline"
          >
            Delete
          </button>
        )}
      </div>
      <div className="mt-4 flex justify-between text-sm text-ink/60">
        <span>{card.cardholder_name}</span>
        <span>{String(card.expiry_month).padStart(2, "0")}/{card.expiry_year}</span>
      </div>
    </div>
  );
}
