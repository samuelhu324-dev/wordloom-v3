/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'http', hostname: 'localhost', port: '18080', pathname: '/uploads/**' },
      { protocol: 'http', hostname: 'localhost', port: '18080', pathname: '/media/**' },
    ],
  },

  async rewrites() {
    return {
      beforeFiles: [
        // Orbit 图片 - 直接转发到后端的 /uploads
        {
          source: "/uploads/:path*",
          destination: "http://localhost:18080/uploads/:path*",
        },
        // Orbit API
        {
          source: "/api/orbit/:path*",
          destination: "http://localhost:18080/api/orbit/:path*",
        },
        // Loom API
        {
          source: "/api/loom/:path*",
          destination: "http://localhost:8013/api/common/:path*",
        },
      ],
    };
  },

  experimental: {
    esmExternals: true,
  },

  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        crypto: false,
      };
    }
    return config;
  },
};

export default nextConfig;
