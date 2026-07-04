/** @type {import('next').NextConfig} */
const nextConfig = {
  // no-store no HTML: o browser sempre busca a página mais recente (que aponta
  // pros chunks do build atual), evitando ChunkLoadError após novos deploys.
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "no-store",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
