export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    container: {
      center: true,
      padding: '1rem',
    },
    extend: {
      colors: {
        hyper: { 
          violet: '#9146FF' 
        },
        electric: { 
          cyan: '#23F0FF' 
        },
        bubblegum: { 
          pink: '#FF5DA2' 
        },
        lime: { 
          slush: '#B3FF38' 
        },
      },
      fontFamily: {
        gen: ['"Sora"', 'ui-sans-serif', 'sans-serif'],
        sans: ['Sora', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'hero-radial': 'radial-gradient(ellipse at top left, var(--tw-gradient-stops))',
        'hero-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'glass-gradient': 'linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))',
      },
      animation: {
        fadeIn: 'fadeIn 0.2s ease-out',
        slideUp: 'slideUp 0.2s ease-out',
        pulseGlow: 'pulseGlow 6s ease-in-out infinite',
        scaleHover: 'scaleHover 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          'from': { opacity: '0' },
          'to': { opacity: '1' },
        },
        slideUp: {
          'from': { opacity: '0', transform: 'translateY(40px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { 
            boxShadow: '0 0 20px rgba(35, 240, 255, 0.3)' 
          },
          '50%': { 
            boxShadow: '0 0 40px rgba(35, 240, 255, 0.6), 0 0 60px rgba(35, 240, 255, 0.4)' 
          },
        },
        scaleHover: {
          '0%': { transform: 'scale(1)' },
          '100%': { transform: 'scale(1.02)' },
        },
      },
      boxShadow: {
        'glass': '0 0 24px 4px rgba(35, 240, 255, 0.25)',
        'glass-hover': '0 0 32px 8px rgba(35, 240, 255, 0.35)',
      },
    },
  },
  plugins: [],
}