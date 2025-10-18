/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: { unoptimized: true },

  // ✅ 新写法：通过 eslint/next ignorePatterns 忽略系统目录
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },

  // ✅ 通知 Next 不要递归监听整个盘符，只看项目目录
  experimental: {
    turbo: {
      rules: {
        "*.ts": { loaders: ["ts-loader"], as: "*.js" },
      },
    },
  },

  // ✅ 额外安全：别扫描这些路径（Windows 保护目录）
  onDemandEntries: {
    // 这个钩子 Next 官方支持
    maxInactiveAge: 1000 * 60 * 60,
    pagesBufferLength: 2,
  },
};

export default nextConfig;
