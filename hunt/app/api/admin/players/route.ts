import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET() {
  try {
    const players = await prisma.player.findMany({
      include: {
        spirits: {
          include: {
            spirit: {
              include: {
                template: true,
              },
            },
          },
        },
      },
      orderBy: {
        createdAt: 'desc',
      },
    })
    return NextResponse.json(players)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch players' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { telegramId, walletAddress } = body

    const player = await prisma.player.create({
      data: {
        telegramId,
        walletAddress,
      },
    })

    return NextResponse.json(player, { status: 201 })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to create player' },
      { status: 500 }
    )
  }
}
