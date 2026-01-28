/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        purple: {
          dark: '#6B21A8',
          DEFAULT: '#9333EA',
          light: '#A855F7',
        },
        navy: {
          dark: '#1E293B',
          DEFAULT: '#334155',
          light: '#475569',
        },
      },
    },
  },
  plugins: [],
}
