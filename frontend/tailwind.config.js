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
          bg: "#FAF9F6",
          card: "#FFFFFF",
          subtle: "#F5F4F0",
          gold: {
            DEFAULT: "#C59A45",
            light: "#DFBD74",
            dark: "#9E7A30",
            bg: "rgba(197, 154, 69, 0.08)",
            border: "rgba(197, 154, 69, 0.35)",
          },
          silver: {
            DEFAULT: "#E3E5E8",
            dark: "#7A828E",
          },
          charcoal: {
            DEFAULT: "#121417",
            body: "#343A40",
            muted: "#6C757D",
          },
          quantum: {
            DEFAULT: "#5B4AE4",
            bg: "rgba(91, 74, 228, 0.06)",
            border: "rgba(91, 74, 228, 0.25)",
          },
          success: {
            DEFAULT: "#198754",
            bg: "rgba(25, 135, 84, 0.08)",
          }
        }
      },
      fontFamily: {
        serif: ['Cinzel', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'qc-sm': '0 2px 8px rgba(0, 0, 0, 0.04)',
        'qc-md': '0 6px 20px rgba(0, 0, 0, 0.06)',
        'qc-lg': '0 12px 36px rgba(0, 0, 0, 0.08)',
        'qc-gold': '0 4px 18px rgba(197, 154, 69, 0.15)',
      }
    },
  },
  plugins: [],
}
