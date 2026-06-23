import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sidebar: {
          DEFAULT: "#1E1B4B",
          dark: "#17144A",
          border: "rgba(255,255,255,0.08)",
        },
        primary: {
          DEFAULT: "#6C63FF",
          from: "#667eea",
          to: "#764ba2",
        },
        surface: "#F8F9FA",
      },
      backgroundImage: {
        "gradient-primary": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "gradient-sidebar": "linear-gradient(180deg, #1E1B4B 0%, #2D2B69 100%)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
