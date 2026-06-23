/** @type {import('next').NextConfig} */

const isTauriBuild = !!process.env.TAURI_ENV_TARGET_TRIPLE;

const nextConfig = isTauriBuild
  ? {
      output: "export",
      trailingSlash: true,
    }
  : {
      async rewrites() {
        return [
          {
            source: "/api/:path*",
            destination: "http://localhost:8001/api/:path*",
          },
        ];
      },
    };

export default nextConfig;
