FROM node:22-slim AS construtor

WORKDIR /app
RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

# o endereço público entra no pacote do navegador no build, porque é assim
# que o Next trata NEXT_PUBLIC_; quem sobe declara em RADAR_API_PUBLICA
ARG RADAR_API_PUBLICA=http://127.0.0.1:8000
ENV NEXT_PUBLIC_API_PUBLICA=$RADAR_API_PUBLICA

RUN pnpm build

FROM node:22-slim AS painel

WORKDIR /app
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

# o standalone traz o servidor e só os módulos que ele usa; estáticos e public
# ficam de fora dele e entram à parte
COPY --from=construtor /app/.next/standalone ./
COPY --from=construtor /app/.next/static ./.next/static
COPY --from=construtor /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
