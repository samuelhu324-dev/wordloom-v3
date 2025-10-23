/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      // Frontend virtual prefix -> Backend real prefix
      { source: "/loom/:path*", destination: "/api/common/:path*" },
    ];
  },
};
export default nextConfig;
