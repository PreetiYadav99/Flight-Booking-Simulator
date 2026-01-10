module.exports = {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Air-branded palette: bright sky blues and soft accents
        primary: '#00ADEF',
        accent: '#0077B6',
        skyLight: '#E6F9FF',
        skyMid: '#CFF4FF'
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui']
      }
    }
  },
  plugins: []
}
