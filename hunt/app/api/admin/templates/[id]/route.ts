import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await request.json()
    const {
      name,
      element,
      rarity,
      generation,
      baseManeuver,
      baseImpulse,
      baseFluidity,
      baseDepth,
      baseReaction,
      baseFlow,
    } = body

    const template = await prisma.spiritTemplate.update({
      where: { id },
      data: {
        name,
        element,
        rarity,
        generation,
        baseManeuver,
        baseImpulse,
        baseFluidity,
        baseDepth,
        baseReaction,
        baseFlow,
      },
    })

    return NextResponse.json(template)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to update template' },
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
    await prisma.spiritTemplate.delete({
      where: { id },
    })

    return NextResponse.json({ success: true })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to delete template' },
      { status: 500 }
    )
  }
}

