/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#0d1117',
        panel: '#161b22',
        accent: '#58a6ff',
        warning: '#e3b341',
        danger: '#f85149',
        success: '#3fb950',
      },
    },
  },
  plugins: [],
}
