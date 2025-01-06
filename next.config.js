/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config, { isServer, dev }) => {
    // Enable detailed webpack logging in development
    if (dev) {
      config.infrastructureLogging = {
        level: 'verbose',
        debug: true,
      };
      
      // Add specific websocket configuration
      config.devServer = {
        ...config.devServer,
        hot: true,
        client: {
          webSocketURL: {
            hostname: 'localhost',
            pathname: '/ws',
            port: 3000,
          },
        },
      };
    }
    return config;
  },
  // Enable more detailed logging
  logging: {
    fetches: {
      fullUrl: true,
    },
  },
  poweredByHeader: false,
}

module.exports = nextConfig
