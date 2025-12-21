import { Server } from 'socket.io'
import { v4 as uuidv4 } from 'uuid'
import { config } from '../config/index.js'
import { FlowFlightRoom } from '../games/flow-flight/FlowFlightRoom.js'
import type { AuthenticatedSocket } from './index.js'

interface QueueEntry {
  socket: AuthenticatedSocket
  gameType: string
  joinedAt: number
}

// Таймеры ожидания перед добавлением ботов
const botFillTimers: Map<string, NodeJS.Timeout> = new Map()

export class Matchmaking {
  private queue: Map<string, QueueEntry> = new Map()
  private rooms: Map<string, FlowFlightRoom> = new Map()
  private playerToRoom: Map<string, string> = new Map()

  addToQueue(socket: AuthenticatedSocket, gameType: string, io: Server) {
    // Проверяем, не в очереди ли уже игрок
    if (this.queue.has(socket.id)) {
      socket.emit('error', { message: 'Already in queue' })
      return
    }

    // Проверяем, не в игре ли уже игрок
    if (this.playerToRoom.has(socket.id)) {
      socket.emit('error', { message: 'Already in a game' })
      return
    }

    this.queue.set(socket.id, {
      socket,
      gameType,
      joinedAt: Date.now(),
    })

    this.notifyQueueStatus(socket, gameType)
    this.tryMatchPlayers(gameType, io)
  }

  removeFromQueue(playerId: string) {
    const entry = this.queue.get(playerId)
    this.queue.delete(playerId)

    // Проверяем, нужно ли отменить таймер ботов
    if (entry && config.bots.enabled) {
      const remainingInQueue = Array.from(this.queue.values())
        .filter(e => e.gameType === entry.gameType).length

      if (remainingInQueue === 0) {
        const timerId = botFillTimers.get(entry.gameType)
        if (timerId) {
          clearTimeout(timerId)
          botFillTimers.delete(entry.gameType)
          console.log(`[Matchmaking] Bot fill timer cancelled for ${entry.gameType}`)
        }
      }
    }
  }

  private notifyQueueStatus(socket: AuthenticatedSocket, gameType: string) {
    const playersInQueue = Array.from(this.queue.values()).filter(
      (entry) => entry.gameType === gameType
    ).length

    socket.emit('queue-status', {
      position: playersInQueue,
      playersNeeded: config.game.playersPerMatch,
      playersInQueue,
    })
  }

  private tryMatchPlayers(gameType: string, io: Server) {
    const queueEntries = Array.from(this.queue.entries())
      .filter(([_, entry]) => entry.gameType === gameType)
      .sort((a, b) => a[1].joinedAt - b[1].joinedAt)

    if (queueEntries.length >= config.game.playersPerMatch) {
      // Достаточно игроков - отменяем таймер ботов если он есть
      const timerId = botFillTimers.get(gameType)
      if (timerId) {
        clearTimeout(timerId)
        botFillTimers.delete(gameType)
      }

      const matchedPlayers = queueEntries.slice(0, config.game.playersPerMatch)
      this.createMatch(matchedPlayers, gameType, io)
    } else if (config.bots.enabled && queueEntries.length > 0 && queueEntries.length < config.game.playersPerMatch) {
      // Не хватает игроков, но режим ботов включен - запускаем таймер
      if (!botFillTimers.has(gameType)) {
        console.log(`[Matchmaking] Starting bot fill timer for ${gameType} (${queueEntries.length} players waiting)`)

        const timerId = setTimeout(() => {
          botFillTimers.delete(gameType)
          this.createMatchWithBots(gameType, io)
        }, config.bots.fillTimeout)

        botFillTimers.set(gameType, timerId)
      }
    }
  }

  private createMatchWithBots(gameType: string, io: Server) {
    const queueEntries = Array.from(this.queue.entries())
      .filter(([_, entry]) => entry.gameType === gameType)
      .sort((a, b) => a[1].joinedAt - b[1].joinedAt)

    if (queueEntries.length === 0) {
      console.log(`[Matchmaking] No players left in queue for bot match`)
      return
    }

    const botsNeeded = config.game.playersPerMatch - queueEntries.length
    console.log(`[Matchmaking] Creating match with ${queueEntries.length} players and ${botsNeeded} bots`)

    // Создаём матч с имеющимися игроками
    this.createMatch(queueEntries, gameType, io, botsNeeded)
  }

  private createMatch(
    players: [string, QueueEntry][],
    gameType: string,
    io: Server,
    botsNeeded: number = 0
  ) {
    const roomId = uuidv4()
    const sockets: AuthenticatedSocket[] = []

    // Удаляем игроков из очереди и собираем сокеты
    for (const [playerId, entry] of players) {
      this.queue.delete(playerId)
      this.playerToRoom.set(playerId, roomId)
      sockets.push(entry.socket)
    }

    console.log(`[Matchmaking] Creating room ${roomId} with ${sockets.length} players` +
      (botsNeeded > 0 ? ` and ${botsNeeded} bots` : ''))

    // Создаём комнату
    if (gameType === 'flow-flight') {
      const room = new FlowFlightRoom(roomId, sockets, io)

      // Добавляем ботов если нужно
      if (botsNeeded > 0) {
        room.addBots(botsNeeded)
      }

      this.rooms.set(roomId, room)

      // Присоединяем всех к Socket.io комнате и отправляем каждому его ID
      for (const socket of sockets) {
        socket.join(roomId)
        // Каждому игроку отправляем его myPlayerId чтобы он знал кто он
        socket.emit('match-found', {
          roomId,
          gameType,
          myPlayerId: socket.id, // ID этого игрока
          players: sockets.map((s) => ({
            id: s.id,
            spiritId: s.player?.spiritId,
          })),
          botsCount: botsNeeded,
        })
      }

      // Запускаем обратный отсчёт
      room.startCountdown()
    }
  }

  getRoom(roomId: string): FlowFlightRoom | undefined {
    return this.rooms.get(roomId)
  }

  getRoomByPlayerId(playerId: string): FlowFlightRoom | undefined {
    const roomId = this.playerToRoom.get(playerId)
    if (roomId) {
      return this.rooms.get(roomId)
    }
    return undefined
  }

  handleDisconnect(playerId: string, io: Server) {
    // Удаляем из очереди если был там
    this.queue.delete(playerId)

    // Обрабатываем выход из комнаты
    const roomId = this.playerToRoom.get(playerId)
    if (roomId) {
      const room = this.rooms.get(roomId)
      if (room) {
        room.handlePlayerDisconnect(playerId)

        // Если комната пуста, удаляем её
        if (room.isEmpty()) {
          this.rooms.delete(roomId)
          console.log(`[Matchmaking] Room ${roomId} deleted (empty)`)
        }
      }
      this.playerToRoom.delete(playerId)
    }
  }

  cleanupRoom(roomId: string) {
    const room = this.rooms.get(roomId)
    if (room) {
      for (const playerId of room.getPlayerIds()) {
        this.playerToRoom.delete(playerId)
      }
      this.rooms.delete(roomId)
      console.log(`[Matchmaking] Room ${roomId} cleaned up`)
    }
  }
}
