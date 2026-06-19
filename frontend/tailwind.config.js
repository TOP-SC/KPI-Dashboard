/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        top: {
          bg: '#0b1220',
          card: '#111b2e',
          border: '#1e2d4a',
          accent: '#3b82f6',
          green: '#22c55e',
          amber: '#f59e0b',
          purple: '#a855f7',
        },
      },
      fontFamily: {
        sans: ['Segoe UI', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
