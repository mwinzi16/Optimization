import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        'bg-primary': '#0a0a0b',
        'bg-secondary': '#111113',
        'bg-card': '#18181b',
        'bg-elevated': '#1f1f23',
        'border-base': '#27272a',
        'border-light': '#3f3f46',
        'text-primary': '#e4e4e7',
        'text-secondary': '#a1a1aa',
        'text-muted': '#71717a',
        'accent-green': '#10B981',
        'accent-teal': '#14B8A6',
        'accent-coral': '#F87171',
        'accent-gold': '#FBBF24',
        'accent-blue': '#3B82F6',
      },
    },
  },
  plugins: [],
} satisfies Config;