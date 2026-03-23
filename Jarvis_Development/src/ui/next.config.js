/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // jarvis-core API proxy (avoids CORS in dev)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/:path*`,
      },
    ];
  },
  webpack(config) {
    // Required for Monaco Editor workers
    config.module.rules.push({
      test: /\.ttf$/,
      type: 'asset/resource',
    });
    return config;
  },
};

module.exports = nextConfig;
