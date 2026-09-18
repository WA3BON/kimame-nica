module.exports = {
  theme: {
    extend: {
      colors: {
        mainGreen: '#4d8b55',
        gold: {
          DEFAULT: '#9e7b3b',
          light: '#c9a668',
          dark: '#7f5b37',
          darker: '#573414',
        },
      },
      animation: {
        'steam': 'steam-up 3s ease-out infinite',
      },
      keyframes: {
        'steam-up': {
          '0%': { opacity: '0', transform: 'translateY(10px) scale(0.9)' },
          '50%': { opacity: '1' },
          '100%': { opacity: '0', transform: 'translateY(-80px) scale(1.2)' },
        },
      },
    },
  },
}