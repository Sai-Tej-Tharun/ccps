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
