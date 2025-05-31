/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./templates/**/*.html",
    "./*/templates/**/*.html", 
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        // Your custom brand colors
        'brand': {
          'primary': '#005F5F',    // main teal
          'secondary': '#009292',  // lighter teal
          'accent': '#606060',     // gray accent
          'light': '#E0F2F1',     // very light teal for backgrounds
          'dark': '#004040',       // darker teal for hover states
        },
        // Override default colors to use your theme
        'primary': {
          50: '#E0F2F1',
          100: '#B2DFDB', 
          200: '#80CBC4',
          300: '#4DB6AC',
          400: '#26A69A',
          500: '#005F5F',  // Your main color
          600: '#00524E',
          700: '#00453E',
          800: '#00392F',
          900: '#002E21',
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}