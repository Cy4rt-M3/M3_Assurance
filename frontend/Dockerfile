FROM oven/bun:1

WORKDIR /app

COPY frontend/package.json frontend/bun.lock ./

RUN bun install --frozen-lockfile

COPY frontend/ ./

RUN bun run build

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

EXPOSE 3000

CMD ["node", ".next/standalone/server.js"]
