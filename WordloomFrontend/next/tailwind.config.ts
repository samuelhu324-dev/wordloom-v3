import type { Config } from "tailwindcss"
import animate from "tailwindcss-animate"   // 新增

const config: Config = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "custom-blue": "#005f7f",
        "custom-green": "#00b894",
        "custom-yellow": "#fbbf24",
        "custom-red": "#f44f5e",
      },
      fontFamily: {
        "sans": ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [
    animate,                               // 新增：启用动画工具类（animate-in/slide/fade等）
  ],
}
export default config