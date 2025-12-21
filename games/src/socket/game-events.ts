import type { AuthenticatedSocket } from './index.js'
import type { Matchmaking } from './matchmaking.js'
import { getStatsDescription, validateStats } from '../games/flow-flight/spirit-stats.js'

interface PlayerInput {
  action?: 'jump'
  direction?: 'up' | 'down' | 'none'
}

interface StatsUpdate {
  targetId?: string // ID игрока или бота (если не указан - свой игрок)
  speed?: number // 0-20
  jump?: number // 0-20
}

/**
 * Socket Events для управления игрой и статами
 *
 * События изменения статов:
 * - 'set-stats' - изменить свои статы (speed, jump)
 * - 'set-participant-stats' - изменить статы любого участника (игрока или бота)
 * - 'get-participants' - получить список всех участников со статами
 * - 'get-stats-info' - получить информацию о влиянии статов
 *
 * Debug события (префикс debug:):
 * - 'debug:set-stats' - тоже что set-participant-stats
 * - 'debug:get-participants' - тоже что get-participants
 */
export function handleGameEvents(socket: AuthenticatedSocket, matchmaking: Matchmaking) {
  // Обработка input от игрока (прыжок или движение)
  socket.on('player-input', (data: PlayerInput) => {
    const room = matchmaking.getRoomByPlayerId(socket.id)
    if (room) {
      room.handlePlayerInput(socket.id, data)
    }
  })

  // Игрок готов к началу
  socket.on('player-ready', () => {
    const room = matchmaking.getRoomByPlayerId(socket.id)
    if (room) {
      room.setPlayerReady(socket.id)
    }
  })

  // === СОБЫТИЯ УПРАВЛЕНИЯ СТАТАМИ ===

  // Изменить свои характеристики
  socket.on('set-stats', (data: { speed?: number; jump?: number }) => {
    const room = matchmaking.getRoomByPlayerId(socket.id)
    if (!room) {
      socket.emit('stats-error', { message: 'Not in a room' })
      return
    }

    if (!validateStats(data)) {
      socket.emit('stats-error', { message: 'Invalid stats values (must be 0-20)' })
      return
    }

    const success = room.setPlayerStats(socket.id, data)
    if (success) {
      const newStats = room.getParticipantStats(socket.id)
      socket.emit('stats-updated', { targetId: socket.id, stats: newStats })
    } else {
      socket.emit('stats-error', { message: 'Failed to update stats' })
    }
  })

  // Изменить характеристики любого участника (игрока или бота)
  socket.on('set-participant-stats', (data: StatsUpdate) => {
    const room = matchmaking.getRoomByPlayerId(socket.id)
    if (!room) {
      socket.emit('stats-error', { message: 'Not in a room' })
      return
    }

    const targetId = data.targetId || socket.id
    const stats = { speed: data.speed, jump: data.jump }

    if (!validateStats(stats)) {
      socket.emit('stats-error', { message: 'Invalid stats values (must be 0-20)' })
      return
    }

    const success = room.setParticipantStats(targetId, stats)
    if (success) {
      const newStats = room.getParticipantStats(targetId)
      socket.emit('stats-updated', { targetId, stats: newStats })
    } else {
      socket.emit('stats-error', { message: 'Target not found' })
    }
  })

  // Получить список всех участников со статами
  socket.on('get-participants', () => {
    const room = matchmaking.getRoomByPlayerId(socket.id)
    if (!room) {
      socket.emit('participants-error', { message: 'Not in a room' })
      return
    }

    const participants = room.getParticipantsWithStats()
    socket.emit('participants', participants)
  })

  // Получить информацию о влиянии статов
  socket.on('get-stats-info', () => {
    const info = getStatsDescription()
    socket.emit('stats-info', info)
  })

  // === DEBUG СОБЫТИЯ (для обратной совместимости) ===

  // Debug: изменение характеристик игрока
  socket.on('debug:set-stats', (data: StatsUpdate) => {
    const room = matchmaking.getRoomByPlayerId(socket.id)
    if (!room) {
      socket.emit('debug:stats-error', { message: 'Not in a room' })
      return
    }

    const targetId = data.targetId || socket.id
    const stats = { speed: data.speed, jump: data.jump }

    if (!validateStats(stats)) {
      socket.emit('debug:stats-error', { message: 'Invalid stats values (must be 0-20)' })
      return
    }

    const success = room.setParticipantStats(targetId, stats)
    if (success) {
      const newStats = room.getParticipantStats(targetId)
      socket.emit('debug:stats-updated', { targetId, stats: newStats })
    } else {
      socket.emit('debug:stats-error', { message: 'Target not found' })
    }
  })

  // Debug: получить всех участников со статами
  socket.on('debug:get-participants', () => {
    const room = matchmaking.getRoomByPlayerId(socket.id)
    if (!room) {
      socket.emit('debug:participants-error', { message: 'Not in a room' })
      return
    }

    const participants = room.getParticipantsWithStats()
    socket.emit('debug:participants', participants)
  })
}
