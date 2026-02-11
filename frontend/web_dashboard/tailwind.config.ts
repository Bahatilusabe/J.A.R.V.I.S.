/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Neon cyan palette
        cyan: {
          50: '#f0fdff',
          100: '#e0fbff',
          200: '#b3f5ff',
          300: '#80ecff',
          400: '#4de3ff',
          500: '#00d9ff', // Primary neon cyan
          600: '#00a8cc',
          700: '#0073a1',
          800: '#004a6b',
          900: '#002a40',
        },
        // Dark navy background
        dark: {
          50: '#f8f9fa',
          100: '#e9ecef',
          200: '#dee2e6',
          300: '#ced4da',
          400: '#adb5bd',
          500: '#6c757d',
          600: '#495057',
          700: '#343a40',
          800: '#212529',
          900: '#0f1724', // Primary dark navy
        },
        // Holographic blue
        holographic: {
          light: '#60a5fa',
          DEFAULT: '#1e90ff',
          dark: '#1566cc',
        },
        // Status colors
        success: '#7be495',
        warning: '#ffa500',
        danger: '#ff6b6b',
        critical: '#ff4444',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
      fontSize: {
        xs: ['0.75rem', { lineHeight: '1rem' }],
        sm: ['0.875rem', { lineHeight: '1.25rem' }],
        base: ['1rem', { lineHeight: '1.5rem' }],
        lg: ['1.125rem', { lineHeight: '1.75rem' }],
        xl: ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
      },
      fontWeight: {
        thin: '100',
        extralight: '200',
        light: '300',
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
        extrabold: '800',
        black: '900',
      },
      boxShadow: {
        'glow-cyan': '0 0 20px rgba(0, 217, 255, 0.4)',
        'glow-blue': '0 0 20px rgba(30, 144, 255, 0.4)',
        'glow-red': '0 0 20px rgba(255, 107, 107, 0.4)',
        'glow-orange': '0 0 20px rgba(255, 165, 0, 0.4)',
        'inner-glow': 'inset 0 0 20px rgba(0, 217, 255, 0.1)',
      },
      backdropBlur: {
        xs: '2px',
        sm: '4px',
        md: '12px',
        lg: '16px',
        xl: '24px',
      },
      animation: {
        pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        spin: 'spin 1s linear infinite',
        bounce: 'bounce 1s infinite',
        glow: 'glow 3s ease-in-out infinite',
      },
      keyframes: {
        glow: {
          '0%, 100%': { opacity: '0.5' },
          '50%': { opacity: '1' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      transitionDuration: {
        150: '150ms',
        200: '200ms',
        300: '300ms',
        400: '400ms',
        500: '500ms',
        700: '700ms',
      },
      zIndex: {
        0: '0',
        10: '10',
        20: '20',
        30: '30',
        40: '40',
        50: '50',
        auto: 'auto',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
  safelist: [
    {
      pattern: /^(bg|text|border|shadow|ring)-(cyan|blue|red|orange|green|yellow|purple|pink|indigo|violet)-\d{1,3}$/,
    },
    {
      pattern: /^(grid-cols|grid-rows)-\d{1,2}$/,
    },
    {
      pattern: /^(w|h|gap)-\d{1,3}(\/\d{1,2})?$/,
    },
  ],
}
