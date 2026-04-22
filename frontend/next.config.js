/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    output: "standalone",
    outputFileTracingRoot: __dirname,
    eslint: {
        ignoreDuringBuilds: true,
    },
};

module.exports = nextConfig;
