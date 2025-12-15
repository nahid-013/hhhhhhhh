# Режимы разработки

## 🚀 Быстрый старт (рекомендуется для разработки)

Только БД в Docker, Next.js локально:

```bash
npm run docker:db
npm install
npx prisma generate
npx prisma migrate dev
npm run dev
```

## 🐳 Варианты запуска

### 1. Только БД в Docker (самый быстрый)
```bash
npm run docker:db
npm run dev
```

### 2. Dev в Docker (с hot-reload)
```bash
npm run docker:dev
```

### 3. Production в Docker (полная сборка)
```bash
npm run docker:prod
```

## ⚡ Оптимизации

- Build-кэш через BuildKit
- Кэширование npm и Next.js
- Standalone output для продакшена
- Multi-stage builds

## 🛑 Остановка

```bash
npm run docker:db:down
docker compose down
docker compose -f docker-compose.dev.yml down
```

