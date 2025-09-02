module.exports = {
  theme: {
    extend: {
      animation: {
        'steam': 'steam-up 3s ease-out infinite',
      },
      keyframes: {
        'steam-up': {
          '0%': { opacity: '0', transform: 'translateY(10px) scale(0.9)' },
          '50%': { opacity: '1' },
          '100%': { opacity: '0', transform: 'translateY(-80px) scale(1.2)' },
        },
      colors: {
        mainGreen: '#4d8b55',
      },
      },
    },
  },
}