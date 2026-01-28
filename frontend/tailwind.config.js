/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Dark theme base colors
        dark: {
          900: '#0a0a0b',   // Deepest background
          800: '#111113',   // Main background
          700: '#18181b',   // Card background
          600: '#1f1f23',   // Elevated surfaces
          500: '#27272a',   // Borders, dividers
          400: '#3f3f46',   // Muted elements
          300: '#52525b',   // Disabled text
          200: '#71717a',   // Secondary text
          100: '#a1a1aa',   // Primary text muted
          50: '#e4e4e7',    // Primary text
        },
        // Schroders Brand Colors (adjusted for dark theme)
        primary: {
          50: '#e6f7ed',
          100: '#ccf0db',
          200: '#99e1b8',
          300: '#66d294',
          400: '#33c371',
          500: '#00A651',   // Schroders Green
          600: '#00C45A',   // Brighter for dark theme
          700: '#00E065',   // Even brighter
          800: '#004d2a',
          900: '#00331c',
        },
        accent: {
          teal: '#14B8A6',
          coral: '#F87171',
          gold: '#FBBF24',
          blue: '#3B82F6',
          purple: '#A855F7',
        },
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
        info: '#0EA5E9',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'glow-green': '0 0 20px rgba(0, 166, 81, 0.3)',
        'glow-teal': '0 0 20px rgba(20, 184, 166, 0.3)',
        'glow-coral': '0 0 20px rgba(248, 113, 113, 0.3)',
        'glow-gold': '0 0 20px rgba(251, 191, 36, 0.3)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
