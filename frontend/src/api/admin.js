import { djangoClient } from "./client";

export const fetchDailySummary = (days = 30) =>
  djangoClient.get("/adminpanel/daily-summary/", { params: { days } }).then((r) => r.data);

export const fetchAdminLogs = () => djangoClient.get("/adminpanel/logs/").then((r) => r.data.results ?? r.data);
// ---- Card management (staff only - the server enforces this, not just the UI) ----
export const fetchAdminCards = (params = {}) =>
  djangoClient.get("/adminpanel/cards/", { params }).then((r) => r.data);

export const blockCard = (id) => djangoClient.post(`/adminpanel/cards/${id}/block/`).then((r) => r.data);

export const unblockCard = (id) => djangoClient.post(`/adminpanel/cards/${id}/unblock/`).then((r) => r.data);

export const updateCardCreditLimit = (id, creditLimit) =>
  djangoClient.patch(`/adminpanel/cards/${id}/credit-limit/`, { credit_limit: creditLimit }).then((r) => r.data);

export const fetchCardActivity = (id, page = 1) =>
  djangoClient.get(`/adminpanel/cards/${id}/activity/`, { params: { page } }).then((r) => r.data);