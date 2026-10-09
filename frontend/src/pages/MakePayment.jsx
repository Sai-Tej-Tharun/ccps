import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listCards } from "../api/cards";
import { extractErrorMessage } from "../api/client";
import { makePayment } from "../api/payments";
import CardTile from "../components/CardTile";
import StatusBadge from "../components/StatusBadge";

export default function MakePayment() {
  const [cards, setCards] = useState([]);
  const [selectedCard, setSelectedCard] = useState(null);
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("OTHER");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    listCards()
      .then((c) => {
        setCards(c);
        setSelectedCard(c.find((card) => !card.is_blocked) ?? null); // never pre-select a blocked card
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    if (!selectedCard) {
      setError("Select a card first.");
      return;
    }
    setSubmitting(true);
    try {
      const payment = await makePayment({ card_id: selectedCard.id, amount, category });
      setResult(payment);
      setAmount("");
    } catch (err) {
      setError(extractErrorMessage(err, "Payment could not be processed."));
    } finally {
      setSubmitting(false);
    }
  };

  if (!loading && cards.length === 0) {
    return (
      <div className="mx-auto max-w-md px-6 py-16 text-center">
        <h1 className="text-xl font-semibold text-ink">No saved cards yet</h1>
        <p className="mt-2 text-sm text-ink/60">Add a card before making a payment.</p>
        <Link to="/cards/add" className="mt-6 inline-block rounded-md bg-ledger-500 px-4 py-2 font-medium text-white hover:bg-ledger-600">
          Add a card
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl px-6 py-10">
      <h1 className="text-2xl font-semibold text-ink">Make a payment</h1>
      <p className="mt-1 text-sm text-ink/60">Simulated processing — no real gateway is used.</p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-6">
        <div>
          <label className="text-sm font-medium text-ink/80">Choose a card</label>
          <div className="mt-2 grid gap-3 sm:grid-cols-2">
            {cards.map((card) => (
              <CardTile
                key={card.id}
                card={card}
                selectable
                selected={selectedCard?.id === card.id}
                onSelect={setSelectedCard}
              />
            ))}
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-ink/80">Amount (USD)</label>
          <input
            type="number"
            required
            min="0.01"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="amount mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
            placeholder="25.00"
          />
          <p className="mt-1 text-xs text-ink/40">Amounts over 5000.00 simulate a decline, for demo purposes.</p>
        </div>

        <div>
          <label htmlFor="category" className="text-sm font-medium text-ink/80">Category</label>
          <select
            id="category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
          >
            <option value="SHOPPING">Shopping</option>
            <option value="FOOD">Food &amp; dining</option>
            <option value="TRAVEL">Travel</option>
            <option value="BILLS">Bills &amp; utilities</option>
            <option value="ENTERTAINMENT">Entertainment</option>
            <option value="HEALTH">Health</option>
            <option value="OTHER">Other</option>
          </select>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-ledger-500 py-2.5 font-medium text-white transition hover:bg-ledger-600 disabled:opacity-60"
        >
          {submitting ? "Processing..." : "Pay now"}
        </button>
      </form>

      {result && (
        <div className="mt-8 rounded-xl border border-ink/10 bg-white p-6">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-lg text-ink">Payment result</h2>
            <StatusBadge status={result.status} />
          </div>
          <dl className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-ink/60">Reference</dt><dd className="font-mono text-ink">{result.reference}</dd></div>
            <div className="flex justify-between"><dt className="text-ink/60">Amount</dt><dd className="amount text-ink">{result.currency} {result.amount}</dd></div>
            {result.failure_reason && (
              <div className="flex justify-between"><dt className="text-ink/60">Reason</dt><dd className="text-danger">{result.failure_reason}</dd></div>
            )}
          </dl>
        </div>
      )}
    </div>
  );
}
