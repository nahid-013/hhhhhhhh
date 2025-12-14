import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET() {
  try {
    const spirits = await prisma.spirit.findMany({
      include: {
        template: true,
        owner: true,
      },
      orderBy: {
        createdAt: 'desc',
      },
    })
    return NextResponse.json(spirits)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch spirits' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const {
      templateId,
      ownerId,
      level = 1,
      xp = 0,
      hunger = 100,
      energy = 100,
      maxEnergy = 100,
      maneuver,
      impulse,
      fluidity,
      depth,
      reaction,
      flow,
    } = body

    if (!templateId) {
      return NextResponse.json(
        { error: 'Template ID is required' },
        { status: 400 }
      )
    }

    const template = await prisma.spiritTemplate.findUnique({
      where: { id: templateId },
    })

    if (!template) {
      return NextResponse.json(
        { error: 'Template not found' },
        { status: 404 }
      )
    }

    const spirit = await prisma.spirit.create({
      data: {
        templateId,
        ownerId: ownerId || null,
        level,
        xp,
        hunger,
        energy,
        maxEnergy,
        maneuver: maneuver ?? template.baseManeuver,
        impulse: impulse ?? template.baseImpulse,
        fluidity: fluidity ?? template.baseFluidity,
        depth: depth ?? template.baseDepth,
        reaction: reaction ?? template.baseReaction,
        flow: flow ?? template.baseFlow,
      },
      include: {
        template: true,
        owner: true,
      },
    })

    return NextResponse.json(spirit, { status: 201 })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to create spirit' },
      { status: 500 }
    )
  }
}
