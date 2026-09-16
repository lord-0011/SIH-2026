/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-page': '#F5F7FA',
        'bg-surface': '#FFFFFF',
        'bg-subtle': '#EEF2F7',
        'border-hairline': '#DCE3EC',
        'text-primary': '#1A2233',
        'text-secondary': '#5A6472',
        'text-muted': '#8A94A6',
        'brand-primary': '#0B4DA2',
        'brand-primary-hover': '#093E82',
        'brand-accent': '#F79A1E',
        'focus-ring': '#2E7CE4',
        'risk-low': '#2E9E5B',
        'risk-low-bg': '#E7F5EC',
        'risk-medium': '#C99A06',
        'risk-medium-bg': '#FBF3D6',
        'risk-high': '#E8730C',
        'risk-high-bg': '#FCE9D6',
        'risk-critical': '#C6362F',
        'risk-critical-bg': '#FBE0DE',
        'data-provisional': '#8A94A6',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
