import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await request.json()
    const { telegramId, walletAddress } = body

    const updateData: any = {}
    if (telegramId !== undefined) updateData.telegramId = telegramId
    if (walletAddress !== undefined) updateData.walletAddress = walletAddress

    const player = await prisma.player.update({
      where: { id },
      data: updateData,
    })

    return NextResponse.json(player)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to update player' },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    
    await prisma.spirit.updateMany({
      where: { ownerId: id },
      data: { ownerId: null },
    })

    await prisma.playerSpirit.deleteMany({
      where: { playerId: id },
    })

    await prisma.player.delete({
      where: { id },
    })

    return NextResponse.json({ success: true })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to delete player' },
      { status: 500 }
    )
  }
}

