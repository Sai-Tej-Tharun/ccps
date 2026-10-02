/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#15231F",
        paper: "#F6F5F1",
        ledger: {
          50: "#EAF2EF",
          100: "#D3E5DE",
          300: "#79AFA0",
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
