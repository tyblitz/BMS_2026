/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        deped: {
          blue: "#0c3b69",
          light: "#e9f2fb",
          gold: "#c59b27",
          dark: "#082542",
        }
      }
    },
  },
  plugins: [],
}
