/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/Images/:path*",
        destination: "/images/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
