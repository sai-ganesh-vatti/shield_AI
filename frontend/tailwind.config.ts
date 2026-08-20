/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0a0a0f',
          800: '#11111a',
          700: '#1a1a2e',
          600: '#24243e',
          500: '#30304a',
          400: '#40405a',
          300: '#5a5a7a',
          200: '#8080a0',
          100: '#a0a0c0',
          50: '#d0d0e0',
        },
        light: {
          900: '#0f0f1a',
          800: '#181824',
          700: '#252535',
          600: '#333345',
          500: '#44445a',
          400: '#5a5a75',
          300: '#8080a0',
          200: '#a0a0c0',
          100: '#d0d0e5',
          50: '#f0f0fa',
        },
        primary: '#00d4aa',
        secondary: '#008ffb',
        accent: '#ff6b6b',
        warning: '#ffa502',
        success: '#00e676',
        info: '#1890ff',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'sans-serif'],
        mono: ['SF Mono', 'Fira Mono', 'monospace'],
      },
    },
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: false,
    styled: true,
    themes: [
      {
        mytheme: {
          primary: 'primary',
          secondary: 'secondary',
          accent: 'accent',
          neutral: 'neutral',
          'base-100': 'base-100',
          info: 'info',
          success: 'success',
          warning: 'warning',
          error: 'error',
        },
      },
    ],
    rtl: false,
  },
}