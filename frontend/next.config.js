/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    output: "standalone",
    outputFileTracingRoot: __dirname,
    eslint: {
        ignoreDuringBuilds: true,
    },
    typescript: {
        // Fail the build immediately on any TypeScript error (e.g. a type error
        // located directly in a critical-path file). Never ignore build errors,
        // including during the incremental allowJs migration.
        ignoreBuildErrors: false,
    },
};

module.exports = nextConfig;
