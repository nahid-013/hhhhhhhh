import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

export async function getPlayerSpirit(playerId: string, spiritId: string) {
  const spirit = await prisma.spirit.findFirst({
    where: {
      id: spiritId,
      ownerId: playerId,
    },
    include: {
      template: true,
    },
  })

  return spirit
}

export async function getSpiritStats(spiritId: string) {
  const spirit = await prisma.spirit.findUnique({
    where: { id: spiritId },
    select: {
      maneuver: true,
      impulse: true,
      fluidity: true,
      depth: true,
      reaction: true,
      flow: true,
      energy: true,
      maxEnergy: true,
    },
  })

  return spirit
}

export async function checkSpiritEnergy(spiritId: string): Promise<boolean> {
  const spirit = await prisma.spirit.findUnique({
    where: { id: spiritId },
    select: { energy: true },
  })

  return spirit ? spirit.energy > 0 : false
}

export async function consumeSpiritEnergy(spiritId: string, amount: number = 10) {
  await prisma.spirit.update({
    where: { id: spiritId },
    data: {
      energy: {
        decrement: amount,
      },
    },
  })
}

export async function addSpiritXP(spiritId: string, xp: number) {
  const spirit = await prisma.spirit.findUnique({
    where: { id: spiritId },
    select: { xp: true, level: true },
  })

  if (!spirit) return

  const newXP = spirit.xp + xp

  // Простая система уровней: 100 XP на 2 уровень, +50 за каждый следующий
  const xpForNextLevel = (level: number) => 100 + (level - 1) * 50
  let currentLevel = spirit.level
  let remainingXP = newXP

  while (remainingXP >= xpForNextLevel(currentLevel) && currentLevel < 10) {
    remainingXP -= xpForNextLevel(currentLevel)
    currentLevel++
  }

  await prisma.spirit.update({
    where: { id: spiritId },
    data: {
      xp: remainingXP,
      level: currentLevel,
    },
  })
}
