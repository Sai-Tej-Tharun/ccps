import { djangoClient } from "./client";

// params: { months, currency, scope }  (scope "all" needs the analytics.view permission)
export const fetchMonthlySummary = (params) =>
  djangoClient.get("/transactions/analytics/monthly/", { params }).then((r) => r.data);

export const fetchCategoryBreakdown = (params) =>
  djangoClient.get("/transactions/analytics/categories/", { params }).then((r) => r.data);

export const fetchUtilization = (params) =>
  djangoClient.get("/transactions/analytics/utilization/", { params }).then((r) => r.data);

// Fetched through the authenticated client as a blob: a plain link would not carry the JWT.
export const downloadAnalyticsExport = async (params, type) => {
  const response = await djangoClient.get("/transactions/analytics/export/", {
    params: { ...params, type },
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = `analytics_summary.${type}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};