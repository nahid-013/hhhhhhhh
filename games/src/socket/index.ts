import { Server, Socket } from 'socket.io'
import { Matchmaking } from './matchmaking.js'
import { handleGameEvents } from './game-events.js'

export interface PlayerData {
  id: string
  sessionId: string
  spiritId: string
  spiritStats?: {
    maneuver: number
    flow: number
    reaction: number
  }
}

export interface AuthenticatedSocket extends Socket {
  player?: PlayerData
}

const matchmaking = new Matchmaking()

export function setupSocketHandlers(io: Server) {
  io.on('connection', (socket: AuthenticatedSocket) => {
    console.log(`[Socket] Client connected: ${socket.id}`)

    // Аутентификация через handshake auth
    const { sessionId, spiritId } = socket.handshake.auth as {
      sessionId?: string
      spiritId?: string
    }

    if (!sessionId || !spiritId) {
      console.log(`[Socket] Missing auth data, disconnecting: ${socket.id}`)
      socket.emit('error', { message: 'Missing sessionId or spiritId' })
      socket.disconnect()
      return
    }

    // Сохраняем данные игрока в сокет
    socket.player = {
      id: socket.id,
      sessionId,
      spiritId,
    }

    console.log(`[Socket] Player authenticated: ${sessionId}, spirit: ${spiritId}`)

    // Обработка присоединения к очереди
    socket.on('join-queue', (gameType: string) => {
      if (gameType !== 'flow-flight') {
        socket.emit('error', { message: 'Unknown game type' })
        return
      }

      console.log(`[Matchmaking] Player ${socket.id} joining queue for ${gameType}`)
      matchmaking.addToQueue(socket, gameType, io)
    })

    // Обработка выхода из очереди
    socket.on('leave-queue', () => {
      console.log(`[Matchmaking] Player ${socket.id} leaving queue`)
      matchmaking.removeFromQueue(socket.id)
      socket.emit('queue-left')
    })

    // Игровые события (input, ready и т.д.)
    handleGameEvents(socket, matchmaking)

    // Обработка отключения
    socket.on('disconnect', (reason) => {
      console.log(`[Socket] Client disconnected: ${socket.id}, reason: ${reason}`)
      matchmaking.handleDisconnect(socket.id, io)
    })
  })
}
