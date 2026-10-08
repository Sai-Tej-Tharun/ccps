/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // These resolve to CSS variables (defined in src/index.css) so they switch with the theme.
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        paper: "rgb(var(--color-paper) / <alpha-value>)",
        ledger: {
          50: "rgb(var(--ledger-50) / <alpha-value>)",
          100: "rgb(var(--ledger-100) / <alpha-value>)",
          300: "rgb(var(--ledger-300) / <alpha-value>)",
          500: "#1F6F5C",
          600: "#195C4C",
          700: "#14493C",
        },
        danger: "#B3261E",
        warn: "#9A6B00",
      },
      fontFamily: {
        serif: ["Fraunces", "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
};
