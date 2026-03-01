import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#13eca4',
        'primary-dark': '#0a8a61',
        'background-dark': '#0a0e14',
        'panel-dark': '#10161f',
        'surface-dark': '#111816',
        'border-dark': '#1e2a3a',
        'text-dim': '#8b9bb4',
        danger: '#ef4444',
        warning: '#ff9a00',
        'accent-red': '#fa5838',
        'accent-green': '#0bda49',
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '0px',
        lg: '0px',
        xl: '0px',
        full: '9999px',
      },
      keyframes: {
        'radar-spin': {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        },
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-glow': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
      },
      animation: {
        'radar-spin': 'radar-spin 2s linear infinite',
        'fade-in': 'fade-in 0.4s ease both',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        blink: 'blink 1s step-end infinite',
        'scroll-logs': 'scroll-logs 20s linear infinite',
      },
    },
  },
  plugins: [],
}

export default config
