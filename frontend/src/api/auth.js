import { djangoClient, tokenStore } from "./client";

export const registerUser = (payload) => djangoClient.post("/auth/register/", payload).then((r) => r.data);

export const loginUser = async ({ email, password }) => {
  const { data } = await djangoClient.post("/auth/login/", { email, password });
  tokenStore.set(data.access, data.refresh);
  return data;
};

export const logoutUser = async () => {
  const refresh = tokenStore.getRefresh();
  try {
    if (refresh) await djangoClient.post("/auth/logout/", { refresh });
  } finally {
    tokenStore.clear();
  }
};

export const fetchCurrentUser = () => djangoClient.get("/auth/me/").then((r) => r.data);
