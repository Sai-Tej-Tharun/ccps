import { djangoClient } from "./client";

export const fetchDailySummary = (days = 30) =>
  djangoClient.get("/adminpanel/daily-summary/", { params: { days } }).then((r) => r.data);

export const fetchAdminLogs = () => djangoClient.get("/adminpanel/logs/").then((r) => r.data.results ?? r.data);
