import express from 'express'
import { createServer } from 'http'
import { Server } from 'socket.io'
import cors from 'cors'
import path from 'path'
import { config } from './config/index.js'
import { setupSocketHandlers } from './socket/index.js'

const app = express()
const httpServer = createServer(app)

const io = new Server(httpServer, {
  cors: config.cors,
  pingTimeout: 60000,
  pingInterval: 25000,
})

app.use(cors(config.cors))
app.use(express.json())

// Статические файлы для Phaser игр
app.use('/games', express.static(path.join(process.cwd(), 'public/games')))

// Health check endpoint
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

// API информация о сервере
app.get('/api/info', (_req, res) => {
  res.json({
    name: 'Hunt Games Service',
    version: '0.1.0',
    games: ['flow-flight'],
  })
})

// Настраиваем Socket.io обработчики
setupSocketHandlers(io)

httpServer.listen(config.port, () => {
  console.log(`[Games Service] Running on port ${config.port}`)
  console.log(`[Games Service] Environment: ${config.nodeEnv}`)
  console.log(`[Games Service] CORS origin: ${config.cors.origin}`)
})

export { io }
