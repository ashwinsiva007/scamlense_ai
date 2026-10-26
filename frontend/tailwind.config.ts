import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F8FAFC",
        text: "#0F172A",
        primary: {
          DEFAULT: "#0F766E",
          hover: "#0D655E",
          light: "#CCFBF1",
        },
        danger: {
          DEFAULT: "#DC2626",
          light: "#FEE2E2",
          dark: "#991B1B",
        },
        warning: {
          DEFAULT: "#D97706",
          light: "#FEF3C7",
          dark: "#92400E",
        },
        info: {
          DEFAULT: "#0369A1",
          light: "#E0F2FE",
          dark: "#075985",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        tamil: ["var(--font-noto-tamil)", "sans-serif"],
        devanagari: ["var(--font-noto-devanagari)", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
