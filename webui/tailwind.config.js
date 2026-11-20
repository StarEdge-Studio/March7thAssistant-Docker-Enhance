/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        m7a: {
          50: '#fdf2f8',
          100: '#fce7f3',
          500: '#ec4899',
          600: '#db2777',
        }
      }
    },
  },
  plugins: [],
}
