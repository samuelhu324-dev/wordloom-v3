/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  compiler: {
    styledComponents: true,
  },
  typescript: {
    tsconfigPath: './tsconfig.json',
  },
  async rewrites() {
    // Same-origin API proxy: maps /api prefix to backend target
    const target = process.env.API_PROXY_TARGET || 'http://localhost:30002';
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
