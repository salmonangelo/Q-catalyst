/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        qc: {
          bg: "#070913",
          surface: "#0D111E",
          card: "rgba(14, 18, 32, 0.82)",
          cardHover: "rgba(22, 28, 48, 0.9)",
          subtle: "#141A2E",
          gold: {
            DEFAULT: "#F59E0B",
            light: "#FDE047",
            dark: "#D97706",
            glow: "rgba(245, 158, 11, 0.25)",
            bg: "rgba(245, 158, 11, 0.08)",
            border: "rgba(245, 158, 11, 0.35)",
          },
          ruby: {
            DEFAULT: "#DC2626",
            light: "#EF4444",
            dark: "#991B1B",
            glow: "rgba(220, 38, 38, 0.25)",
            bg: "rgba(220, 38, 38, 0.1)",
            border: "rgba(220, 38, 38, 0.35)",
          },
          silver: {
            DEFAULT: "#CBD5E1",
            light: "#F8FAFC",
            dark: "#64748B",
            border: "rgba(203, 213, 225, 0.15)",
          },
          cyan: {
            DEFAULT: "#06B6D4",
            light: "#38BDF8",
            bg: "rgba(6, 182, 212, 0.08)",
            border: "rgba(6, 182, 212, 0.3)",
          },
          charcoal: {
            DEFAULT: "#0B0E17",
            body: "#94A3B8",
            muted: "#64748B",
          },
          quantum: {
            DEFAULT: "#818CF8",
            light: "#A5B4FC",
            bg: "rgba(129, 140, 248, 0.08)",
            border: "rgba(129, 140, 248, 0.25)",
          },
          success: {
            DEFAULT: "#10B981",
            light: "#34D399",
            bg: "rgba(16, 185, 129, 0.1)",
            border: "rgba(16, 185, 129, 0.3)",
          }
        }
      },
      fontFamily: {
        serif: ['Cinzel', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'qc-sm': '0 2px 10px rgba(0, 0, 0, 0.35)',
        'qc-md': '0 8px 30px rgba(0, 0, 0, 0.5)',
        'qc-lg': '0 16px 48px rgba(0, 0, 0, 0.65)',
        'qc-gold': '0 0 25px rgba(245, 158, 11, 0.25)',
        'qc-ruby': '0 0 25px rgba(220, 38, 38, 0.25)',
        'qc-cyan': '0 0 25px rgba(6, 182, 212, 0.25)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      }
    },
  },
  plugins: [],
}
