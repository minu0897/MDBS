FROM node:20-slim
WORKDIR /app

COPY FE/package.json FE/package-lock.json* ./
RUN npm ci

COPY FE/ .

ENV HOSTNAME=0.0.0.0
EXPOSE 5173
CMD ["npm","run","dev"]
