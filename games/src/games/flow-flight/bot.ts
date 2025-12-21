import { config } from '../../config/index.js'
import type { Obstacle } from './obstacles.js'
import {
  GameStats,
  generateBotStats,
  calculateSpeed,
  calculateJumpSpeedMultiplier,
} from './spirit-stats.js'

// Физика прыжка (базовые значения)
const JUMP_CONFIG = {
  playerSize: 40,
}

// Единая дорожка для всех игроков
const SINGLE_TRACK = { y: 300, groundY: 330 }

export interface BotState {
  id: string
  name: string
  spiritId: string
  y: number
  baseY: number
  velocityY: number
  isJumping: boolean
  distance: number
  isAlive: boolean
  isReady: boolean
  isBot: true
  stats: GameStats // Игровые характеристики (speed, jump 0-20)
  // Внутреннее состояние бота
  nextJumpDistance: number | null // На какой дистанции нужно прыгнуть
  skillLevel: number // 0-1, насколько хорошо бот играет (1 = идеально)
}

let botIdCounter = 0

// Функция для генерации случайного значения в диапазоне
function randomInRange(min: number, max: number): number {
  return min + Math.random() * (max - min)
}

export function createBot(): BotState {
  // Все боты на единой дорожке
  const baseY = SINGLE_TRACK.groundY - JUMP_CONFIG.playerSize / 2
  const botId = `bot_${++botIdCounter}_${Date.now()}`
  const botName = config.bots.names[botIdCounter % config.bots.names.length]

  // Случайный уровень скилла из конфига
  const { min: skillMin, max: skillMax } = config.bots.skillLevel
  const skillLevel = skillMin + Math.random() * (skillMax - skillMin)

  return {
    id: botId,
    name: botName,
    spiritId: `bot_spirit_${botIdCounter}`,
    y: baseY,
    baseY,
    velocityY: 0,
    isJumping: false,
    distance: 0,
    isAlive: true,
    isReady: true,
    isBot: true,
    stats: generateBotStats(),
    nextJumpDistance: null,
    skillLevel,
  }
}

// Рассчитывает, когда боту нужно прыгнуть
export function updateBotAI(bot: BotState, obstacles: Obstacle[]): boolean {
  if (!bot.isAlive || bot.isJumping) return false

  // Скорость бота
  const baseSpeed = calculateSpeed(bot.stats)

  // Множитель скорости во время прыжка (замедление)
  const jumpSpeedMultiplier = calculateJumpSpeedMultiplier(bot.stats)

  // Если уже запланирован прыжок - проверяем, пора ли
  if (bot.nextJumpDistance !== null) {
    if (bot.distance >= bot.nextJumpDistance) {
      bot.nextJumpDistance = null // Сбрасываем после прыжка
      return true
    }
    return false
  }

  // Находим ближайшее препятствие (кроме птиц - под ними пробегаем)
  let nearestObstacle: Obstacle | null = null
  let minDistance = Infinity

  for (const obs of obstacles) {
    if (obs.type === 'bird') continue // Птиц пропускаем под ними

    const dist = obs.x - bot.distance
    if (dist > 0 && dist < config.bots.reactionDistance && dist < minDistance) {
      minDistance = dist
      nearestObstacle = obs
    }
  }

  if (!nearestObstacle) {
    return false
  }

  // Рассчитываем когда нужно прыгнуть
  // Время до пика прыжка ~0.4с (постоянное)
  const timeToJumpPeak = 0.4

  // Во время прыжка скорость уменьшается, поэтому дистанция меньше
  const speedDuringJump = baseSpeed * jumpSpeedMultiplier
  const distanceToJumpPeak = speedDuringJump * timeToJumpPeak

  // Прыгаем когда до препятствия осталось distanceToJumpPeak + ширина препятствия/2
  const jumpDistance = nearestObstacle.x - distanceToJumpPeak - nearestObstacle.width / 2

  // Добавляем небольшую случайность на основе skillLevel (лучшие боты прыгают точнее)
  const variance = config.bots.reactionVariance * (1 - bot.skillLevel)
  const randomOffset = (Math.random() - 0.5) * variance

  // Запоминаем когда прыгать
  bot.nextJumpDistance = jumpDistance + randomOffset

  // Если уже пора прыгать - прыгаем сразу
  if (bot.distance >= bot.nextJumpDistance) {
    bot.nextJumpDistance = null
    return true
  }

  return false
}

// Рассчитывает высоту прыжка (одинаковая для всех, т.к. v и g масштабируются одинаково)
export function calculateJumpHeight(): number {
  // h = v^2 / (2 * g) где v = |baseJumpForce|, g = baseGravity
  // При масштабировании: h = (v*k)^2 / (2 * g*k) = v^2 / (2*g) - высота не меняется
  const baseJumpForce = config.flowFlight.baseJumpForce
  const baseGravity = config.flowFlight.baseGravity
  return (baseJumpForce * baseJumpForce) / (2 * baseGravity)
}
