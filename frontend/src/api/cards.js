import { djangoClient } from "./client";

export const listCards = () => djangoClient.get("/cards/").then((r) => r.data.results ?? r.data);

export const addCard = (payload) => djangoClient.post("/cards/", payload).then((r) => r.data);

export const deleteCard = (id) => djangoClient.delete(`/cards/${id}/`);
