# dev에서 사용하는 react docker file
FROM node:20-slim AS base
WORKDIR /app
# 의존성 설치 캐시 최적화
COPY FE/package.json FE/package-lock.json* ./ 
RUN npm ci
# 소스 복사 및 핫리로드
COPY FE/ .
EXPOSE 5173
CMD ["npm", "run", "dev"]

