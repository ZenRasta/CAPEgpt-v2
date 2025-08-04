export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    container: { center: true, padding: { DEFAULT: '1rem', lg: '2rem' } },
    extend: {
      colors: {
        brand: { blue: '#3B82F6', indigo: '#6366F1', bg: '#F5F7FB' },
      },
      backgroundImage: {
        'hero-gradient': 'linear-gradient(135deg,#3B82F6 0%,#6366F1 100%)',
      },
      borderRadius: { '3xl': '1.5rem' },
      boxShadow: {
        soft: '0 10px 30px rgba(0,0,0,0.08)',
        card: '0 15px 40px rgba(2,15,46,0.08)',
        pill: '0 8px 20px rgba(59,130,246,0.35)',
      },
      letterSpacing: { tightish: '-0.01em' },
    },
  },
  plugins: [],
} 