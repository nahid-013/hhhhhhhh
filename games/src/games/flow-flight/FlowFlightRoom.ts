import { Server } from 'socket.io'
import { config } from '../../config/index.js'
import { generateObstacles, Obstacle } from './obstacles.js'
import { calculateRewards, PlayerResult } from './scoring.js'
import { createBot, updateBotAI, BotState } from './bot.js'
import {
  GameStats,
  createTestingStats,
  updateStats,
  calculateSpeed,
  calculateJumpForce,
  calculateGravity,
  calculateJumpSpeedMultiplier,
  getStatsDescription,
  validateStats,
} from './spirit-stats.js'
import type { AuthenticatedSocket } from '../../socket/index.js'

// Единая дорожка для всех игроков (все бегут по одной линии)
const SINGLE_TRACK = { y: 300, groundY: 330 }

// Физика прыжка (базовые значения, реальные зависят от статов)
const JUMP_CONFIG = {
  playerSize: 40,
}

interface PlayerState {
  id: string
  spiritId: string
  y: number // Текущая Y позиция (для прыжка)
  baseY: number // Позиция на земле
  velocityY: number // Вертикальная скорость
  isJumping: boolean
  distance: number // Пройденная дистанция
  isAlive: boolean
  isReady: boolean
  isBot?: boolean
  stats: GameStats // Характеристики (speed, jump 0-20)
}

type GamePhase = 'waiting' | 'countdown' | 'playing' | 'finished'

export class FlowFlightRoom {
  private roomId: string
  private players: Map<string, PlayerState> = new Map()
  private bots: Map<string, BotState> = new Map() // Хранилище ботов
  private sockets: Map<string, AuthenticatedSocket> = new Map()
  private io: Server
  private phase: GamePhase = 'waiting'
  private obstacles: Obstacle[] = []
  private gameTime: number = 0
  private seed: number
  private gameLoop: NodeJS.Timeout | null = null
  private lastUpdate: number = 0

  constructor(roomId: string, sockets: AuthenticatedSocket[], io: Server) {
    this.roomId = roomId
    this.io = io
    this.seed = Date.now()

    // Все игроки начинают с одной точки на единой дорожке
    const baseY = SINGLE_TRACK.groundY - JUMP_CONFIG.playerSize / 2

    sockets.forEach((socket) => {
      this.sockets.set(socket.id, socket)

      this.players.set(socket.id, {
        id: socket.id,
        spiritId: socket.player?.spiritId || '',
        y: baseY,
        baseY: baseY,
        velocityY: 0,
        isJumping: false,
        distance: 0,
        isAlive: true,
        isReady: false,
        stats: createTestingStats(),
      })
    })
  }

  // Добавить ботов в комнату (все на одной дорожке)
  addBots(count: number) {
    for (let i = 0; i < count; i++) {
      const bot = createBot()
      this.bots.set(bot.id, bot)
      console.log(`[FlowFlight] Bot ${bot.name} added to room ${this.roomId}`)
    }
  }

  // Получить количество игроков (реальных + ботов)
  getTotalPlayerCount(): number {
    return this.players.size + this.bots.size
  }

  // Получить количество реальных игроков
  getRealPlayerCount(): number {
    return this.players.size
  }

  startCountdown() {
    this.phase = 'countdown'
    let count = config.game.countdownSeconds

    const countdownInterval = setInterval(() => {
      this.io.to(this.roomId).emit('game-countdown', { count })
      count--

      if (count < 0) {
        clearInterval(countdownInterval)
        this.startGame()
      }
    }, 1000)
  }

  private startGame() {
    this.phase = 'playing'
    this.lastUpdate = Date.now()
    this.obstacles = generateObstacles(this.seed)
    console.log(`[FlowFlight] Game started in room ${this.roomId}, finishDistance: ${config.flowFlight.finishDistance}`)

    // Собираем всех участников (игроков + ботов)
    const allParticipants = [
      ...Array.from(this.players.values()).map((p) => ({
        id: p.id,
        spiritId: p.spiritId,
        y: p.y,
        stats: p.stats,
        isBot: false,
      })),
      ...Array.from(this.bots.values()).map((b) => ({
        id: b.id,
        spiritId: b.spiritId,
        y: b.y,
        stats: b.stats,
        isBot: true,
        name: b.name,
      })),
    ]

    const noObstacles = config.testing?.noObstacles || false
    const obstacleSettings = {
      count: config.obstacles?.count || 50,
      minSpacing: config.obstacles?.minSpacing || 150,
      safeZoneStart: config.obstacles?.safeZoneStart || 500,
    }
    console.log(`[FlowFlight] Starting game with noObstacles=${noObstacles}, obstacles:`, obstacleSettings)

    this.io.to(this.roomId).emit('game-start', {
      seed: this.seed,
      players: allParticipants,
      finishDistance: config.flowFlight.finishDistance,
      noObstacles,
      obstacleSettings,
    })

    // Запускаем игровой цикл
    const tickInterval = 1000 / config.game.tickRate
    this.gameLoop = setInterval(() => this.update(), tickInterval)
  }

  private update() {
    if (this.phase !== 'playing') return

    const now = Date.now()
    const deltaTime = (now - this.lastUpdate) / 1000
    this.lastUpdate = now
    this.gameTime += deltaTime

    // Обновляем позиции игроков
    for (const player of this.players.values()) {
      if (!player.isAlive) continue

      // Скорость зависит от стата speed
      let speed = calculateSpeed(player.stats)

      // Во время прыжка скорость замедляется (jump уменьшает замедление)
      if (player.isJumping) {
        const jumpSpeedMultiplier = calculateJumpSpeedMultiplier(player.stats)
        speed *= jumpSpeedMultiplier
      }

      player.distance += speed * deltaTime

      // Физика прыжка
      if (player.isJumping) {
        const gravity = calculateGravity()
        player.velocityY += gravity * deltaTime
        player.y += player.velocityY * deltaTime

        // Приземление
        if (player.y >= player.baseY) {
          player.y = player.baseY
          player.velocityY = 0
          player.isJumping = false
        }
      }

      // Проверка столкновений
      const collision = this.checkCollision(player)
      if (collision) {
        player.isAlive = false
        console.log(`[Collision] Player ${player.id} hit obstacle:`, {
          playerDistance: Math.floor(player.distance),
          playerY: Math.floor(player.y),
          playerBaseY: player.baseY,
          isJumping: player.isJumping,
          obstacle: collision,
        })
        this.io.to(this.roomId).emit('player-eliminated', {
          playerId: player.id,
          distance: Math.floor(player.distance),
        })
      }
    }

    // Обновляем ботов
    for (const bot of this.bots.values()) {
      if (!bot.isAlive) continue

      // AI принимает решение о прыжке
      if (updateBotAI(bot, this.obstacles)) {
        bot.isJumping = true
        bot.velocityY = calculateJumpForce()
      }

      // Скорость зависит от стата speed
      let speed = calculateSpeed(bot.stats)

      // Во время прыжка скорость замедляется (jump уменьшает замедление)
      if (bot.isJumping) {
        const jumpSpeedMultiplier = calculateJumpSpeedMultiplier(bot.stats)
        speed *= jumpSpeedMultiplier
      }

      bot.distance += speed * deltaTime

      // Физика прыжка
      if (bot.isJumping) {
        const gravity = calculateGravity()
        bot.velocityY += gravity * deltaTime
        bot.y += bot.velocityY * deltaTime

        // Приземление
        if (bot.y >= bot.baseY) {
          bot.y = bot.baseY
          bot.velocityY = 0
          bot.isJumping = false
        }
      }

      // Проверка столкновений
      if (this.checkBotCollision(bot)) {
        bot.isAlive = false
        this.io.to(this.roomId).emit('player-eliminated', {
          playerId: bot.id,
          distance: Math.floor(bot.distance),
          isBot: true,
        })
      }
    }

    // Отправляем состояние игры
    this.broadcastGameState()

    // Проверяем финиш - кто-то достиг финишной дистанции
    const finishDistance = config.flowFlight.finishDistance

    // Проверяем всех участников на достижение финиша
    let someoneFinished = false

    for (const player of this.players.values()) {
      if (player.isAlive && player.distance >= finishDistance) {
        console.log(`[FlowFlight] Player ${player.id} reached finish at ${Math.floor(player.distance)}/${finishDistance}`)
        someoneFinished = true
      }
    }

    for (const bot of this.bots.values()) {
      if (bot.isAlive && bot.distance >= finishDistance) {
        console.log(`[FlowFlight] Bot ${bot.id} reached finish at ${Math.floor(bot.distance)}/${finishDistance}`)
        someoneFinished = true
      }
    }

    if (someoneFinished) {
      console.log(`[FlowFlight] Ending game - someone crossed the finish line!`)
      // Останавливаем всех на финише
      for (const player of this.players.values()) {
        if (player.distance >= finishDistance) {
          player.distance = finishDistance
        }
      }
      for (const bot of this.bots.values()) {
        if (bot.distance >= finishDistance) {
          bot.distance = finishDistance
        }
      }
      this.endGame()
      return
    }

    // Проверяем конец игры (все игроки и боты мертвы)
    const alivePlayers = Array.from(this.players.values()).filter((p) => p.isAlive)
    const aliveBots = Array.from(this.bots.values()).filter((b) => b.isAlive)
    if (alivePlayers.length === 0 && aliveBots.length === 0) {
      this.endGame()
    }
  }

  private checkBotCollision(bot: BotState): boolean {
    const playerRadius = JUMP_CONFIG.playerSize / 2
    // Позиция игрока по X = его дистанция
    const playerLeft = bot.distance - playerRadius
    const playerRight = bot.distance + playerRadius
    const playerTop = bot.y - playerRadius
    const playerBottom = bot.y + playerRadius

    for (const obstacle of this.obstacles) {
      // Пропускаем препятствия вне зоны проверки
      if (obstacle.x < playerLeft - 100 || obstacle.x > playerRight + 100) continue

      const obsLeft = obstacle.x - obstacle.width / 2
      const obsRight = obstacle.x + obstacle.width / 2
      const obsTop = obstacle.y
      const obsBottom = obstacle.y + obstacle.height

      // AABB collision
      if (
        playerRight > obsLeft &&
        playerLeft < obsRight &&
        playerBottom > obsTop &&
        playerTop < obsBottom
      ) {
        return true
      }
    }

    return false
  }

  private checkCollision(player: PlayerState): Obstacle | null {
    const playerRadius = JUMP_CONFIG.playerSize / 2
    // Позиция игрока по X = его дистанция (пройденное расстояние от старта)
    const playerLeft = player.distance - playerRadius
    const playerRight = player.distance + playerRadius
    const playerTop = player.y - playerRadius
    const playerBottom = player.y + playerRadius

    for (const obstacle of this.obstacles) {
      // Пропускаем препятствия вне зоны проверки
      if (obstacle.x < playerLeft - 100 || obstacle.x > playerRight + 100) continue

      // AABB collision - препятствие как прямоугольник
      const obsLeft = obstacle.x - obstacle.width / 2
      const obsRight = obstacle.x + obstacle.width / 2
      const obsTop = obstacle.y
      const obsBottom = obstacle.y + obstacle.height

      // Проверка пересечения прямоугольников
      if (
        playerRight > obsLeft &&
        playerLeft < obsRight &&
        playerBottom > obsTop &&
        playerTop < obsBottom
      ) {
        return obstacle
      }
    }

    return null
  }

  private broadcastGameState() {
    // Собираем всех участников (игроков + ботов)
    const allParticipants = [
      ...Array.from(this.players.values()).map((p) => ({
        id: p.id,
        y: p.y,
        distance: Math.floor(p.distance),
        isAlive: p.isAlive,
        isJumping: p.isJumping,
        isBot: false,
      })),
      ...Array.from(this.bots.values()).map((b) => ({
        id: b.id,
        y: b.y,
        distance: Math.floor(b.distance),
        isAlive: b.isAlive,
        isJumping: b.isJumping,
        isBot: true,
      })),
    ]

    const state = {
      gameTime: this.gameTime,
      players: allParticipants,
    }

    this.io.to(this.roomId).emit('game-state', state)
  }

  private endGame() {
    if (this.gameLoop) {
      clearInterval(this.gameLoop)
      this.gameLoop = null
    }

    this.phase = 'finished'

    // Собираем всех участников (игроков + ботов) и сортируем по дистанции
    const allParticipants = [
      ...Array.from(this.players.values()).map((p) => ({
        id: p.id,
        spiritId: p.spiritId,
        distance: p.distance,
        isBot: false,
      })),
      ...Array.from(this.bots.values()).map((b) => ({
        id: b.id,
        spiritId: b.spiritId,
        distance: b.distance,
        isBot: true,
      })),
    ].sort((a, b) => b.distance - a.distance)

    const results: PlayerResult[] = allParticipants.map((p, index) => ({
      playerId: p.id,
      spiritId: p.spiritId,
      distance: Math.floor(p.distance),
      place: index + 1,
      isBot: p.isBot,
    }))

    // Рассчитываем награды (только для реальных игроков)
    const realPlayerResults = results.filter(r => !r.isBot)
    const rewards = calculateRewards(realPlayerResults)

    this.io.to(this.roomId).emit('game-end', {
      results,
      rewards,
    })

    console.log(`[FlowFlight] Game ended in room ${this.roomId}`, results)
  }

  // Обработка прыжка
  handlePlayerInput(playerId: string, input: { action?: string; direction?: string }) {
    const player = this.players.get(playerId)
    if (!player || !player.isAlive) return

    const jumpForce = calculateJumpForce()

    // Прыжок
    if (input.action === 'jump' && !player.isJumping) {
      player.isJumping = true
      player.velocityY = jumpForce
    }

    // Поддержка старого формата (direction) для обратной совместимости
    if (input.direction === 'up' && !player.isJumping) {
      player.isJumping = true
      player.velocityY = jumpForce
    }
  }

  // Метод для изменения характеристик игрока
  setPlayerStats(playerId: string, stats: Partial<GameStats>): boolean {
    const player = this.players.get(playerId)
    if (!player) return false

    if (!validateStats(stats)) {
      console.log(`[FlowFlight] Invalid stats for player ${playerId}:`, stats)
      return false
    }

    player.stats = updateStats(player.stats, stats)
    console.log(`[FlowFlight] Player ${playerId} stats updated:`, player.stats)
    return true
  }

  // Метод для изменения характеристик бота
  setBotStats(botId: string, stats: Partial<GameStats>): boolean {
    const bot = this.bots.get(botId)
    if (!bot) return false

    if (!validateStats(stats)) {
      console.log(`[FlowFlight] Invalid stats for bot ${botId}:`, stats)
      return false
    }

    bot.stats = updateStats(bot.stats, stats)
    console.log(`[FlowFlight] Bot ${bot.name} stats updated:`, bot.stats)
    return true
  }

  // Установить полные статы для участника (игрока или бота)
  setParticipantStats(participantId: string, stats: Partial<GameStats>): boolean {
    return this.setPlayerStats(participantId, stats) || this.setBotStats(participantId, stats)
  }

  // Получить статы участника
  getParticipantStats(participantId: string): GameStats | null {
    const player = this.players.get(participantId)
    if (player) return { ...player.stats }

    const bot = this.bots.get(participantId)
    if (bot) return { ...bot.stats }

    return null
  }

  // Получить всех игроков и ботов со статами
  getParticipantsWithStats() {
    const statsDescription = getStatsDescription()
    return {
      players: Array.from(this.players.values()).map((p) => ({
        id: p.id,
        spiritId: p.spiritId,
        isBot: false,
        stats: p.stats,
        calculatedSpeed: calculateSpeed(p.stats),
        jumpSpeedMultiplier: calculateJumpSpeedMultiplier(p.stats),
      })),
      bots: Array.from(this.bots.values()).map((b) => ({
        id: b.id,
        name: b.name,
        isBot: true,
        stats: b.stats,
        calculatedSpeed: calculateSpeed(b.stats),
        jumpSpeedMultiplier: calculateJumpSpeedMultiplier(b.stats),
      })),
      statsInfo: statsDescription,
    }
  }

  setPlayerReady(playerId: string) {
    const player = this.players.get(playerId)
    if (player) {
      player.isReady = true
    }
  }

  handlePlayerDisconnect(playerId: string) {
    const player = this.players.get(playerId)
    if (player) {
      player.isAlive = false
      this.io.to(this.roomId).emit('player-disconnected', { playerId })
    }
    this.sockets.delete(playerId)
  }

  isEmpty(): boolean {
    return this.sockets.size === 0
  }

  getPlayerIds(): string[] {
    return Array.from(this.players.keys())
  }
}
