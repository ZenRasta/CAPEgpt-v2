/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    container: { 
      center: true, 
      padding: { 
        DEFAULT: '1rem', 
        lg: '2rem' 
      } 
    },
    extend: {
      fontFamily: { 
        display: ['Poppins', 'ui-sans-serif', 'system-ui'],
        sans: ['Poppins', 'ui-sans-serif', 'system-ui']
      },
      colors: {
        brand: {
          blue: '#3B82F6',   // header + accents
          indigo: '#6366F1', // gradient end
          bg: '#F5F7FB',     // section banding
        },
      },
      boxShadow: {
        soft: '0 10px 30px rgba(0,0,0,0.08)',
        card: '0 15px 40px rgba(2,15,46,0.08)',
        pill: '0 8px 20px rgba(59,130,246,0.35)',
      },
      borderRadius: { 
        '3xl': '1.5rem' 
      },
      backgroundImage: {
        'hero-gradient': 'linear-gradient(135deg, #3B82F6 0%, #6366F1 100%)',
      },
      letterSpacing: { 
        tightish: '-0.01em' 
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
} 