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
      onClick={() => selectable && onSelect?.(card)}
      className={`rounded-xl border p-5 transition ${
        selectable ? "cursor-pointer hover:border-ledger-400" : ""
      } ${selected ? "border-ledger-500 ring-2 ring-ledger-200" : "border-ink/10"} bg-white`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-ink/50">{BRAND_LABEL[card.brand] || card.brand}</p>
          <p className="amount mt-1 text-lg text-ink">{card.masked_number}</p>
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
