import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET() {
  try {
    const templates = await prisma.spiritTemplate.findMany({
      orderBy: {
        createdAt: 'desc',
      },
    })
    return NextResponse.json(templates)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch templates' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const {
      name,
      element,
      rarity,
      generation = 1,
      baseManeuver,
      baseImpulse,
      baseFluidity,
      baseDepth,
      baseReaction,
      baseFlow,
    } = body

    if (!name || !element || !rarity) {
      return NextResponse.json(
        { error: 'Name, element, and rarity are required' },
        { status: 400 }
      )
    }

    const template = await prisma.spiritTemplate.create({
      data: {
        name,
        element,
        rarity,
        generation,
        baseManeuver: baseManeuver || 10,
        baseImpulse: baseImpulse || 10,
        baseFluidity: baseFluidity || 10,
        baseDepth: baseDepth || 10,
        baseReaction: baseReaction || 10,
        baseFlow: baseFlow || 10,
      },
    })

    return NextResponse.json(template, { status: 201 })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to create template' },
      { status: 500 }
    )
  }
}
