/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        background: 'rgb(var(--color-bg) / <alpha-value>)',
        surface: 'rgb(var(--color-surface) / <alpha-value>)',
        'surface-deep': 'rgb(var(--color-surface-deep) / <alpha-value>)',
        primary: 'rgb(var(--color-primary) / <alpha-value>)',
        electric: 'rgb(var(--color-electric) / <alpha-value>)',
        honey: 'rgb(var(--color-honey) / <alpha-value>)',
        foreground: 'rgb(var(--color-text) / <alpha-value>)',
        muted: 'rgb(var(--color-muted) / <alpha-value>)',
        border: 'rgb(var(--color-border) / <alpha-value>)'
      },
      boxShadow: {
        glow: '0 0 40px var(--shadow-glow)',
        premium: '0 24px 80px rgba(2, 6, 23, 0.36)'
      },
      fontFamily: {
        sans: ['Inter', 'Sarabun', 'ui-sans-serif', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: []
};
