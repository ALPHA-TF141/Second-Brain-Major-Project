/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#070A12',
        panel: '#111827',
        cyanGlow: '#35D8FF',
        mintGlow: '#5EF2B8',
        warningGlow: '#FFC857'
      },
      boxShadow: {
        glow: '0 0 35px rgba(53, 216, 255, 0.18)',
        soft: '0 18px 60px rgba(0, 0, 0, 0.28)'
      },
      fontFamily: {
        display: ['Inter', 'ui-sans-serif', 'system-ui'],
        body: ['Inter', 'ui-sans-serif', 'system-ui']
      }
    }
  },
  plugins: []
};
