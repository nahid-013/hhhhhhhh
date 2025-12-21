export interface PlayerResult {
  playerId: string
  spiritId: string
  distance: number
  place: number // 1, 2, 3
  isBot?: boolean // Является ли игрок ботом
}

export interface PlayerReward {
  playerId: string
  lumens: number
  xp: number
  ton: number // редкая награда TON
  hasPulseCapsule: boolean
}

export function calculateRewards(results: PlayerResult[]): PlayerReward[] {
  return results.map((result) => {
    let lumens = 0
    let xp = 0
    let ton = 0
    let hasPulseCapsule = false

    // Базовые награды за участие
    const baseXp = 10
    const baseLumens = 50

    switch (result.place) {
      case 1:
        // 1 место - много Люменов + шанс на TON и Пульс-капсулу
        lumens = baseLumens * 5 + Math.floor(result.distance / 100)
        xp = baseXp * 3
        ton = Math.random() < 0.05 ? 0.1 : 0 // 5% шанс на 0.1 TON
        hasPulseCapsule = Math.random() < 0.1 // 10% шанс
        break

      case 2:
        // 2 место - Люмены + шанс на буст/TON
        lumens = baseLumens * 3 + Math.floor(result.distance / 150)
        xp = baseXp * 2
        ton = Math.random() < 0.02 ? 0.05 : 0 // 2% шанс на 0.05 TON
        hasPulseCapsule = Math.random() < 0.03 // 3% шанс
        break

      case 3:
        // 3 место - базовые Люмены
        lumens = baseLumens + Math.floor(result.distance / 200)
        xp = baseXp
        break

      default:
        // На случай если игроков больше 3
        lumens = Math.floor(baseLumens / 2)
        xp = Math.floor(baseXp / 2)
    }

    return {
      playerId: result.playerId,
      lumens,
      xp,
      ton,
      hasPulseCapsule,
    }
  })
}
