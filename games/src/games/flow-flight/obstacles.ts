import { config } from '../../config/index.js'

// Единая дорожка для всех игроков
const SINGLE_TRACK = { y: 300, groundY: 330 }

export interface Obstacle {
  id: number
  x: number      // Позиция по горизонтали (дистанция от старта)
  y: number      // Позиция по вертикали
  width: number
  height: number
  type: 'cactus' | 'rock' | 'bird'
}

// Простой PRNG для детерминированной генерации
function seededRandom(seed: number): () => number {
  let state = seed
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296
    return state / 4294967296
  }
}

export function generateObstacles(seed: number): Obstacle[] {
  // Отладка
  console.log('[Obstacles] config.obstacles:', config.obstacles)
  console.log('[Obstacles] noObstacles:', config.testing?.noObstacles)

  // Если включён режим без препятствий или count = 0
  if (config.testing?.noObstacles || config.obstacles?.count === 0) {
    console.log('[Obstacles] NO OBSTACLES MODE - returning empty array')
    return []
  }

  const random = seededRandom(seed)
  const obstacles: Obstacle[] = []

  // Настройки из конфига
  const obstacleCount = config.obstacles?.count || 50
  const minSpacing = config.obstacles?.minSpacing || 150
  const safeZoneStart = config.obstacles?.safeZoneStart || 500
  const finishDistance = config.flowFlight?.finishDistance || 3000

  // Зона для размещения препятствий
  const availableDistance = finishDistance - safeZoneStart - 100 // -100 чтобы не было прямо на финише

  console.log(`[Obstacles] Generating ${obstacleCount} obstacles on single track from ${safeZoneStart} to ${finishDistance}`)

  let obstacleId = 0
  const trackPositions: number[] = []

  // Генерируем позиции для единой дорожки
  for (let i = 0; i < obstacleCount; i++) {
    // Равномерно распределяем + случайный сдвиг
    const basePosition = safeZoneStart + (availableDistance / obstacleCount) * i
    const randomOffset = (random() - 0.5) * (availableDistance / obstacleCount) * 0.5
    let x = basePosition + randomOffset

    // Проверяем минимальное расстояние от предыдущих
    for (const prevX of trackPositions) {
      if (Math.abs(x - prevX) < minSpacing) {
        x = prevX + minSpacing + random() * 50
      }
    }

    // Не выходим за границы
    x = Math.max(safeZoneStart, Math.min(x, finishDistance - 100))
    trackPositions.push(x)
  }

  // Сортируем позиции
  trackPositions.sort((a, b) => a - b)

  // Создаём препятствия на единой дорожке
  for (const x of trackPositions) {
    // Тип препятствия (cactus - 60%, rock - 24%, bird - 16%)
    const typeRoll = random()
    const obstacleType: 'cactus' | 'rock' | 'bird' =
      typeRoll < 0.6 ? 'cactus' : typeRoll < 0.84 ? 'rock' : 'bird'

    // Размер и позиция Y зависят от типа
    let width: number, height: number, y: number
    switch (obstacleType) {
      case 'cactus':
        width = 20 + random() * 15
        height = 40 + random() * 30
        y = SINGLE_TRACK.groundY - height
        break
      case 'rock':
        width = 30 + random() * 20
        height = 25 + random() * 15
        y = SINGLE_TRACK.groundY - height
        break
      case 'bird':
        width = 25
        height = 20
        y = SINGLE_TRACK.groundY - 60 - random() * 30
        break
    }

    obstacles.push({
      id: obstacleId++,
      x,
      y,
      width,
      height,
      type: obstacleType,
    })
  }

  console.log(`[Obstacles] Generated ${obstacles.length} obstacles`)
  return obstacles
}

// Получить препятствия в видимой области
export function getVisibleObstacles(
  obstacles: Obstacle[],
  cameraX: number,
  viewWidth: number
): Obstacle[] {
  const margin = 100
  return obstacles.filter(
    (obs) => obs.x >= cameraX - margin && obs.x <= cameraX + viewWidth + margin
  )
}
