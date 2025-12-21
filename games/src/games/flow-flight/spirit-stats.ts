/**
 * Spirit Stats Module
 *
 * Централизованный модуль для управления характеристиками спиритов.
 * Обеспечивает маппинг характеристик из БД на игровые статы.
 *
 * Характеристики спирита из БД:
 * - maneuver (маневренность) - влияет на скорость
 * - impulse (импульс) - влияет на прыжок
 * - fluidity (плавность) - влияет на скорость
 * - depth (глубина) - запас
 * - reaction (реакция) - влияет на прыжок
 * - flow (поток) - влияет на скорость
 *
 * Игровые статы:
 * - speed (0-20) - скорость бега
 * - jump (0-20) - сила прыжка
 */

import { config } from '../../config/index.js'

// Характеристики спирита из БД
export interface SpiritAttributes {
  maneuver: number
  impulse: number
  fluidity: number
  depth: number
  reaction: number
  flow: number
}

// Игровые статы
export interface GameStats {
  speed: number // 0-20, влияет на скорость бега
  jump: number // 0-20, влияет на силу прыжка
}

// Конфигурация маппинга
export interface StatMappingConfig {
  speed: {
    attributes: Array<keyof SpiritAttributes>
    weights: number[]
    scale: number // Делитель для нормализации к 0-20
  }
  jump: {
    attributes: Array<keyof SpiritAttributes>
    weights: number[]
    scale: number
  }
}

// Дефолтный конфиг маппинга (можно переопределить)
const defaultMapping: StatMappingConfig = {
  speed: {
    // Скорость зависит от: flow (основной) + maneuver + fluidity
    attributes: ['flow', 'maneuver', 'fluidity'],
    weights: [0.5, 0.3, 0.2],
    scale: 5, // Делим сумму на 5 для получения значения 0-20
  },
  jump: {
    // Прыжок зависит от: impulse (основной) + reaction
    attributes: ['impulse', 'reaction'],
    weights: [0.7, 0.3],
    scale: 5,
  },
}

/**
 * Маппит характеристики спирита из БД на игровые статы
 */
export function mapSpiritToGameStats(
  spirit: SpiritAttributes,
  mappingConfig: StatMappingConfig = defaultMapping
): GameStats {
  const calculateStat = (
    statConfig: StatMappingConfig['speed'] | StatMappingConfig['jump']
  ): number => {
    let weightedSum = 0

    for (let i = 0; i < statConfig.attributes.length; i++) {
      const attr = statConfig.attributes[i]
      const weight = statConfig.weights[i] || 1 / statConfig.attributes.length
      weightedSum += spirit[attr] * weight
    }

    // Нормализуем к диапазону 0-20
    const normalized = Math.round(weightedSum / statConfig.scale)
    return Math.max(0, Math.min(20, normalized))
  }

  return {
    speed: calculateStat(mappingConfig.speed),
    jump: calculateStat(mappingConfig.jump),
  }
}

/**
 * Создает дефолтные статы (для новых игроков без спирита)
 */
export function createDefaultStats(): GameStats {
  return {
    speed: config.stats.defaultSpeed,
    jump: config.stats.defaultJump,
  }
}

/**
 * Создает статы для тестирования.
 * Если testing.enabled = true, использует testing.myStats
 * Иначе возвращает дефолтные статы
 */
export function createTestingStats(): GameStats {
  if (config.testing?.enabled) {
    return {
      speed: config.testing.myStats.speed,
      jump: config.testing.myStats.jump,
    }
  }
  return createDefaultStats()
}

/**
 * Генерирует случайные статы для ботов в заданном диапазоне
 */
export function generateBotStats(): GameStats {
  const { speed: speedRange, jump: jumpRange } = config.bots.stats

  return {
    speed: randomInRange(speedRange.min, speedRange.max),
    jump: randomInRange(jumpRange.min, jumpRange.max),
  }
}

/**
 * Создает статы с заданными значениями (для тестирования/дебага)
 */
export function createStats(speed: number, jump: number): GameStats {
  return {
    speed: clamp(speed),
    jump: clamp(jump),
  }
}

/**
 * Обновляет статы, сохраняя те что не указаны
 */
export function updateStats(
  current: GameStats,
  updates: Partial<GameStats>
): GameStats {
  return {
    speed: updates.speed !== undefined ? clamp(updates.speed) : current.speed,
    jump: updates.jump !== undefined ? clamp(updates.jump) : current.jump,
  }
}

/**
 * Рассчитывает реальную скорость на основе стата
 */
export function calculateSpeed(stats: GameStats): number {
  return config.flowFlight.baseSpeed + stats.speed * config.flowFlight.speedStatMultiplier
}

/**
 * Рассчитывает множитель скорости ВО ВРЕМЯ прыжка.
 * Прыжок замедляет спирита, но высокий jump уменьшает это замедление.
 *
 * jump=1   -> multiplier=0.5 (50% скорости, сильное замедление)
 * jump=50  -> multiplier=0.75 (75% скорости)
 * jump=100 -> multiplier=1.0 (100% скорости, без замедления)
 */
export function calculateJumpSpeedMultiplier(stats: GameStats): number {
  const { min, max } = config.stats
  const slowdownBase = config.flowFlight.jumpSlowdownBase // 0.5 = 50% замедление при jump=1

  // Нормализуем jump от 0 до 1, где min=0, max=1
  const normalized = (stats.jump - min) / (max - min)

  // При jump=1: multiplier = 1 - 0.5 = 0.5 (50% скорости)
  // При jump=100: multiplier = 1 - 0 = 1.0 (100% скорости)
  return 1 - slowdownBase * (1 - normalized)
}

/**
 * Возвращает базовую силу прыжка (одинаковая для всех)
 */
export function calculateJumpForce(): number {
  return config.flowFlight.baseJumpForce
}

/**
 * Возвращает базовую гравитацию (одинаковая для всех)
 */
export function calculateGravity(): number {
  return config.flowFlight.baseGravity
}

/**
 * Получить описание влияния статов
 */
export function getStatsDescription(): {
  speed: { base: number; multiplier: number; description: string }
  jump: { slowdown: number; description: string }
} {
  const slowdownPercent = Math.round(config.flowFlight.jumpSlowdownBase * 100)
  return {
    speed: {
      base: config.flowFlight.baseSpeed,
      multiplier: config.flowFlight.speedStatMultiplier,
      description: `Скорость = ${config.flowFlight.baseSpeed} + (speed * ${config.flowFlight.speedStatMultiplier}) px/s`,
    },
    jump: {
      slowdown: config.flowFlight.jumpSlowdownBase,
      description: `Замедление при прыжке: jump=1 → -${slowdownPercent}%, jump=100 → 0% (без замедления)`,
    },
  }
}

/**
 * Валидирует статы
 */
export function validateStats(stats: Partial<GameStats>): boolean {
  const { min, max } = config.stats
  if (stats.speed !== undefined && (stats.speed < min || stats.speed > max)) {
    return false
  }
  if (stats.jump !== undefined && (stats.jump < min || stats.jump > max)) {
    return false
  }
  return true
}

// Хелперы
function randomInRange(min: number, max: number): number {
  return min + Math.floor(Math.random() * (max - min + 1))
}

function clamp(value: number): number {
  return Math.max(config.stats.min, Math.min(config.stats.max, value))
}
