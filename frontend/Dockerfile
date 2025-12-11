FROM node:18-alpine

WORKDIR /app

# 先拷贝 package.json 和本地依赖目录
COPY package.json pnpm-lock.yaml* ./
COPY eslint-rules ./eslint-rules

# 安装依赖（不带 --frozen-lockfile，方便没有 lockfile 的情况）
RUN corepack enable && pnpm install || pnpm install

# 再拷贝剩余源码
COPY . .

CMD ["pnpm", "dev"]