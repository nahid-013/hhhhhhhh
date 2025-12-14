import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await request.json()
    const { spiritId, slotIndex, isActive = false } = body

    if (!spiritId) {
      return NextResponse.json(
        { error: 'Spirit ID is required' },
        { status: 400 }
      )
    }

    const player = await prisma.player.findUnique({
      where: { id },
    })

    if (!player) {
      return NextResponse.json(
        { error: 'Player not found' },
        { status: 404 }
      )
    }

    const spirit = await prisma.spirit.findUnique({
      where: { id: spiritId },
    })

    if (!spirit) {
      return NextResponse.json(
        { error: 'Spirit not found' },
        { status: 404 }
      )
    }

    await prisma.spirit.update({
      where: { id: spiritId },
      data: { ownerId: id },
    })

    const playerSpirit = await prisma.playerSpirit.upsert({
      where: {
        playerId_spiritId: {
          playerId: id,
          spiritId: spiritId,
        },
      },
      update: {
        slotIndex,
        isActive,
      },
      create: {
        playerId: id,
        spiritId: spiritId,
        slotIndex,
        isActive,
      },
      include: {
        spirit: {
          include: {
            template: true,
          },
        },
      },
    })

    return NextResponse.json(playerSpirit, { status: 201 })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to add spirit to player' },
      { status: 500 }
    )
  }
}
