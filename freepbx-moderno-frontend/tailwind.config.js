/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  darkMode: 'class', // Tu configuración actual
  theme: {
    extend: {
      colors: {
        primary: "#4338ca",
        "primary-hover": "#3730a3",
        "background-light": "#f3f4f6",
        "background-dark": "#0f172a",
        "sidebar-dark": "#1e1e2d",
        "card-light": "#ffffff",
        "card-dark": "#1e293b",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
}
