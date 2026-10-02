import { fastapiClient } from "./client";

export const makePayment = (payload) => fastapiClient.post("/payments/pay", payload).then((r) => r.data);

export const listMyPayments = () => fastapiClient.get("/payments/").then((r) => r.data);
