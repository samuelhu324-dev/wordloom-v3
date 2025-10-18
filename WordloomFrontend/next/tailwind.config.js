/** @type {import('tailwindcss').Config} */
module.exports = {
  // 仅扫描本项目代码，避免误扫磁盘根目录
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#1E40AF",
        accent:  "#475569",
        meta:    "#6B7280",
      },
      fontFamily: {
        // 与你 assets/static/fonts 的中文衬线思路保持一致
        serif: ["'Noto Serif SC'", "serif"],
      },
    },
  },
  plugins: [],
};
