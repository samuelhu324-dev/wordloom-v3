/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  distDir: process.env.NEXT_DIST_DIR || '.next',
  compiler: {
    styledComponents: true,
  },
  turbopack: {
    root: path.join(__dirname),
  },
  typescript: {
    tsconfigPath: './tsconfig.json',
  },
  async rewrites() {
    // Same-origin API proxy: maps /api prefix to backend target
    const target =
      process.env.API_PROXY_TARGET ||
      process.env.NEXT_PUBLIC_API_BASE ||
      'http://localhost:30001';
    const prefix = process.env.API_PROXY_PREFIX || '/api/v1';
    // Ensure prefix starts with slash
    const normalizedPrefix = prefix.startsWith('/') ? prefix : `/${prefix}`;
    return [
      {
        source: `${normalizedPrefix}/:path*`,
        destination: `${target}${normalizedPrefix}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
