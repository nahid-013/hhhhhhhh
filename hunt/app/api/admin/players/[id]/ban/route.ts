import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await request.json()
    const { reason } = body

    const player = await prisma.player.update({
      where: { id },
      data: {
        isBanned: true,
        bannedAt: new Date(),
        banReason: reason || null,
      },
    })

    return NextResponse.json(player)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to ban player' },
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

    const player = await prisma.player.update({
      where: { id },
      data: {
        isBanned: false,
        bannedAt: null,
        banReason: null,
      },
    })

    return NextResponse.json(player)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to unban player' },
      { status: 500 }
    )
  }
}
