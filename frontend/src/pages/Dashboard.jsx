import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listCards } from "../api/cards";
import { listMyPayments } from "../api/payments";
import StatusBadge from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();
  const [cards, setCards] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listCards(), listMyPayments()])
      .then(([c, p]) => {
        setCards(c);
        setPayments(p.slice(0, 5));
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-semibold text-ink">Welcome, {user?.first_name || user?.email}</h1>
      <p className="mt-1 text-ink/60">Here's a quick look at your account.</p>

      <div className="mt-8 grid gap-6 sm:grid-cols-2">
        <div className="rounded-xl border border-ink/10 bg-white p-6">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-lg text-ink">Saved Cards</h2>
            <Link to="/cards/add" className="text-sm font-medium text-ledger-600 hover:underline">+ Add card</Link>
          </div>
          {loading ? (
            <p className="mt-4 text-sm text-ink/50">Loading...</p>
          ) : cards.length === 0 ? (
            <p className="mt-4 text-sm text-ink/50">No cards yet — add one to make a payment.</p>
          ) : (
            <p className="mt-4 text-3xl font-semibold text-ink">{cards.length}</p>
          )}
        </div>

        <div className="rounded-xl border border-ink/10 bg-white p-6">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-lg text-ink">Make a Payment</h2>
            <Link to="/payments/new" className="text-sm font-medium text-ledger-600 hover:underline">New payment →</Link>
          </div>
          <p className="mt-4 text-sm text-ink/60">Pay using any of your saved cards.</p>
        </div>
      </div>

      <div className="mt-8 rounded-xl border border-ink/10 bg-white p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-serif text-lg text-ink">Recent Activity</h2>
          <Link to="/transactions" className="text-sm font-medium text-ledger-600 hover:underline">View all →</Link>
        </div>

        {loading ? (
          <p className="mt-4 text-sm text-ink/50">Loading...</p>
        ) : payments.length === 0 ? (
          <p className="mt-4 text-sm text-ink/50">No payments yet.</p>
        ) : (
          <table className="mt-4 w-full text-sm">
            <tbody>
              {payments.map((p) => (
                <tr key={p.id} className="border-t border-ink/5">
                  <td className="py-3 text-ink/60">{new Date(p.created_at).toLocaleString()}</td>
                  <td className="amount py-3 text-ink">{p.currency} {p.amount}</td>
                  <td className="py-3"><StatusBadge status={p.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
