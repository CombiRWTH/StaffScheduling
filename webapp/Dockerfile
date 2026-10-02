FROM node:26.10.0-bookworm-slim

WORKDIR /app
RUN npm install --global pnpm@12.8.1
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
CMD ["pnpm", "run", "dev", "--hostname", "0.0.0.0"]
