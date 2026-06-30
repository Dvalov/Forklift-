/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#121C2E',
        panel: '#0a0e1a',
        accent: '#00ffff',
        warning: '#ffaa00',
        danger: '#ff3366',
        success: '#3fb950',
        cyan: '#00ffff',
        'accent-warn': '#ffaa00',
        'accent-err': '#ff3366',
      },
    },
  },
  plugins: [],
}
