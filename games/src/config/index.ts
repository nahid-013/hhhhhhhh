import { convertToLegacyConfig } from './game-settings'

// Получаем настройки из удобного файла game-settings.ts
const settings = convertToLegacyConfig()

export const config = {
  port: parseInt(process.env.PORT || '9000', 10),
  nodeEnv: process.env.NODE_ENV || 'development',
  cors: {
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    credentials: true,
  },
  // Все настройки игры берутся из game-settings.ts
  ...settings,
}
