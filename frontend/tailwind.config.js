/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        feents: {
          50:  '#E5FAF6',
          100: '#C2F2E8',
          DEFAULT: '#00D1B2',
          600: '#00B89C',
          700: '#009A82',
        },
        fs: {
          25:  '#FBFCFD',
          50:  '#F5F7FA',
          100: '#EEF1F5',
          200: '#E2E7EE',
          300: '#C9D1DC',
          400: '#97A2B2',
          500: '#6B7585',
          600: '#4A5566',
          700: '#2E3744',
          800: '#1A2330',
          900: '#0B1220',
        },
      },
      fontFamily: {
        sans: [
          'Pretendard Variable', 'Pretendard',
          '-apple-system', 'BlinkMacSystemFont',
          'Apple SD Gothic Neo', 'Noto Sans KR',
          'Helvetica Neue', 'Arial', 'sans-serif',
        ],
        mono: [
          'JetBrains Mono', 'ui-monospace', 'SFMono-Regular',
          'Menlo', 'SF Mono', 'Monaco', 'Consolas', 'monospace',
        ],
      },
    },
  },
  plugins: [],
}
