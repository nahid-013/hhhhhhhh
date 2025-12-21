import { addSpiritXP, consumeSpiritEnergy } from './player.service.js'

export interface GameReward {
  playerId: string
  spiritId: string
  lumens: number
  xp: number
  ton: number
  hasPulseCapsule: boolean
}

export async function applyGameRewards(rewards: GameReward[]) {
  for (const reward of rewards) {
    try {
      // Добавляем XP спириту
      if (reward.xp > 0) {
        await addSpiritXP(reward.spiritId, reward.xp)
      }

      // Уменьшаем энергию спирита после игры
      await consumeSpiritEnergy(reward.spiritId, 10)

      // TODO: Добавить Люмены игроку (требуется поле lumens в Player)
      // TODO: Добавить TON игроку (требуется поле tonBalance в Player)
      // TODO: Добавить Пульс-капсулу в инвентарь игрока

      console.log(`[Rewards] Applied rewards for player ${reward.playerId}:`, {
        xp: reward.xp,
        lumens: reward.lumens,
        ton: reward.ton,
        hasPulseCapsule: reward.hasPulseCapsule,
      })
    } catch (error) {
      console.error(`[Rewards] Failed to apply rewards for player ${reward.playerId}:`, error)
    }
  }
}
