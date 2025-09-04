/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',        // 정적 export → out/ 폴더 생성
  basePath: '/mdbs',       
  assetPrefix: '/mdbs/',   // 정적 자산 경로 접두사
  images: { unoptimized: true }, // next/image 사용 시 필수(정적 export)
  trailingSlash: true,     
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
}

export default nextConfig
