import { fastapiClient } from "./client";

export const getDashboardSummary = () => fastapiClient.get("/dashboard/summary").then((r) => r.data);