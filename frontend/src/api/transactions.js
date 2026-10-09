import { djangoClient } from "./client";

// filters: { status, date_from, date_to, min_amount, max_amount }
export const listTransactions = (filters = {}) =>
  djangoClient.get("/transactions/", { params: filters }).then((r) => r.data.results ?? r.data);

// A plain <a href> to this endpoint would NOT carry the JWT (the API
// authenticates via an Authorization header, not a cookie, so a bare
// browser navigation arrives unauthenticated). Instead, fetch it through
// the authenticated axios client as a blob and trigger the download
// client-side.
export const downloadTransactionsCsv = async (filters = {}) => {
  const response = await djangoClient.get("/transactions/export/", {
    params: filters,
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data], { type: "text/csv" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "transactions_export.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
// Same approach as the CSV export: fetch through the authenticated client as a
// blob (a plain link would not carry the JWT), then trigger the download.
export const downloadMonthlyStatement = async ({ year, month }) => {
  const response = await djangoClient.get("/transactions/statement/", {
    params: { year, month },
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `statement_${year}_${String(month).padStart(2, "0")}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
// Paged search. params: status, category, fraud_status, card, date_from, date_to,
// min_amount, max_amount, ordering, page, page_size. Returns { count, next, previous, results }.
export const searchTransactions = (params = {}) =>
  djangoClient.get("/transactions/", { params }).then((r) => r.data);