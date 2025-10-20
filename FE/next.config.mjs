/** Next 15: dev는 basePath/assetPrefix 끄고, prod에서만 /mdbs 사용 */
const isProd = process.env.NODE_ENV === 'production';

export default {
  pageExtensions: ['js', 'jsx', 'ts', 'tsx'],

  ...(isProd
    ? {
        basePath: '/mdbs',
        assetPrefix: '/mdbs/',
        trailingSlash: true,
        images: { unoptimized: true },
        output: 'export',
      }
    : {}),
};
