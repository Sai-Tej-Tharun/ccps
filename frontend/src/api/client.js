import axios from "axios";

// Two backends: Django (auth/cards/transactions/admin) and FastAPI
// (payment processing only). Both read the same JWT from localStorage.
export const DJANGO_BASE_URL = import.meta.env.VITE_DJANGO_API_URL || "http://localhost:8000/api";
export const FASTAPI_BASE_URL = import.meta.env.VITE_FASTAPI_API_URL || "http://localhost:8001";

const ACCESS_KEY = "ccps_access_token";
const REFRESH_KEY = "ccps_refresh_token";

export const tokenStore = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access, refresh) => {
    localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

function createClient(baseURL) {
  const instance = axios.create({ baseURL });

  instance.interceptors.request.use((config) => {
    const token = tokenStore.getAccess();
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

  // On a 401, try exactly one silent refresh (against Django, the only
  // issuer of tokens) before giving up and forcing a re-login.
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const original = error.config;
      if (error.response?.status === 401 && !original._retried && tokenStore.getRefresh()) {
        original._retried = true;
        try {
          const { data } = await axios.post(`${DJANGO_BASE_URL}/auth/refresh/`, {
            refresh: tokenStore.getRefresh(),
          });
          tokenStore.set(data.access, data.refresh);
          original.headers.Authorization = `Bearer ${data.access}`;
          return instance(original);
        } catch {
          tokenStore.clear();
          window.location.href = "/login";
        }
      }
      return Promise.reject(error);
    }
  );

  return instance;
}

export const djangoClient = createClient(DJANGO_BASE_URL);
export const fastapiClient = createClient(FASTAPI_BASE_URL);

// A single place to turn any backend error payload into one readable
// string, since Django (DRF) and FastAPI shape validation errors
// differently.
export function extractErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  const data = error?.response?.data;
  if (!data) return fallback;
  if (typeof data === "string") return data;
  if (data.detail) {
    return typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
  }
  // DRF validation errors: { field: ["message"] }
  const firstKey = Object.keys(data)[0];
  if (firstKey && Array.isArray(data[firstKey])) return data[firstKey][0];
  if (firstKey && typeof data[firstKey] === "string") return data[firstKey];
  return fallback;
}
