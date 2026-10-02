import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { addCard } from "../api/cards";
import { extractErrorMessage } from "../api/client";

const MONTHS = Array.from({ length: 12 }, (_, i) => i + 1);
const YEARS = Array.from({ length: 16 }, (_, i) => new Date().getFullYear() + i);

export default function AddCard() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    card_number: "",
    cvv: "",
    cardholder_name: "",
    expiry_month: new Date().getMonth() + 1,
    expiry_year: new Date().getFullYear(),
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await addCard({
        ...form,
        expiry_month: Number(form.expiry_month),
        expiry_year: Number(form.expiry_year),
      });
      navigate("/dashboard");
    } catch (err) {
      setError(extractErrorMessage(err, "Could not add this card."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-6 py-10">
      <h1 className="text-2xl font-semibold text-ink">Add a card</h1>
      <p className="mt-1 text-sm text-ink/60">
        Only the card's brand and last 4 digits are stored — the full number and CVV are never saved.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-4">
        <div>
          <label className="text-sm font-medium text-ink/80">Card number</label>
          <input
            required
            inputMode="numeric"
            placeholder="4111 1111 1111 1111"
            value={form.card_number}
            onChange={update("card_number")}
            className="amount mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
          />
          <p className="mt-1 text-xs text-ink/40">
            Demo values: end in 0002/0069/0127 to simulate a decline later; any other valid number simulates success.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="col-span-2">
            <label className="text-sm font-medium text-ink/80">Cardholder name</label>
            <input
              required
              value={form.cardholder_name}
              onChange={update("cardholder_name")}
              className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-ink/80">CVV</label>
            <input
              required
              inputMode="numeric"
              maxLength={4}
              value={form.cvv}
              onChange={update("cvv")}
              className="amount mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm font-medium text-ink/80">Expiry month</label>
            <select
              value={form.expiry_month}
              onChange={update("expiry_month")}
              className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
            >
              {MONTHS.map((m) => <option key={m} value={m}>{String(m).padStart(2, "0")}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-ink/80">Expiry year</label>
            <select
              value={form.expiry_year}
              onChange={update("expiry_year")}
              className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 outline-none focus:border-ledger-500"
            >
              {YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-ledger-500 py-2.5 font-medium text-white transition hover:bg-ledger-600 disabled:opacity-60"
        >
          {submitting ? "Adding..." : "Add card"}
        </button>
      </form>
    </div>
  );
}
