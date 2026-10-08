import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

export const THEME_STORAGE_KEY = "ccps_theme";

const ThemeContext = createContext(null);

const isTheme = (value) => value === "light" || value === "dark";

// localStorage can throw (private mode, blocked site data) - never let that break the app.
function readStoredTheme() {
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
    return isTheme(stored) ? stored : null;
  } catch {
    return null;
  }
}

function writeStoredTheme(theme) {
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    /* persistence is best-effort */
  }
}

const systemTheme = () =>
  window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";

export function ThemeProvider({ children }) {
  // Saved choice wins; otherwise follow the operating system.
  const [theme, setThemeState] = useState(() => readStoredTheme() ?? systemTheme());
  const transitionTimer = useRef(null);

  // Apply to <html>. The inline script in index.html already did this before
  // first paint, so there is no flash of the wrong theme on reload.
  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", theme === "dark");
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute("content", theme === "dark" ? "#0E1512" : "#F6F5F1");
  }, [theme]);

  // Follow OS changes while the user has not chosen explicitly.
  useEffect(() => {
    const query = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!query) return undefined;
    const onChange = (event) => {
      if (!readStoredTheme()) setThemeState(event.matches ? "dark" : "light");
    };
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  // Keep several open tabs in sync.
  useEffect(() => {
    const onStorage = (event) => {
      if (event.key === THEME_STORAGE_KEY && isTheme(event.newValue)) setThemeState(event.newValue);
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  useEffect(() => () => window.clearTimeout(transitionTimer.current), []);

  const setTheme = useCallback((next) => {
    if (!isTheme(next)) return;
    // The .theme-transition class (index.css) enables colour transitions for
    // a moment only, so ordinary hover effects elsewhere are unaffected.
    const root = document.documentElement;
    root.classList.add("theme-transition");
    window.clearTimeout(transitionTimer.current);
    transitionTimer.current = window.setTimeout(() => root.classList.remove("theme-transition"), 350);
    writeStoredTheme(next);
    setThemeState(next);
  }, []);

  const toggleTheme = useCallback(() => setTheme(theme === "dark" ? "light" : "dark"), [theme, setTheme]);

  const value = useMemo(
    () => ({ theme, isDark: theme === "dark", setTheme, toggleTheme }),
    [theme, setTheme, toggleTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within a ThemeProvider");
  return ctx;
}