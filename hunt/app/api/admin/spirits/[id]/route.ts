import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const spirit = await prisma.spirit.findUnique({
      where: { id },
      include: {
        template: true,
        owner: true,
      },
    })

    if (!spirit) {
      return NextResponse.json(
        { error: 'Spirit not found' },
        { status: 404 }
      )
    }

    return NextResponse.json(spirit)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch spirit' },
      { status: 500 }
    )
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await request.json()
    const {
      level,
      xp,
      hunger,
      energy,
      maxEnergy,
      maneuver,
      impulse,
      fluidity,
      depth,
      reaction,
      flow,
      ownerId,
    } = body

    const updateData: any = {}
    if (level !== undefined) updateData.level = level
    if (xp !== undefined) updateData.xp = xp
    if (hunger !== undefined) updateData.hunger = hunger
    if (energy !== undefined) updateData.energy = energy
    if (maxEnergy !== undefined) updateData.maxEnergy = maxEnergy
    if (maneuver !== undefined) updateData.maneuver = maneuver
    if (impulse !== undefined) updateData.impulse = impulse
    if (fluidity !== undefined) updateData.fluidity = fluidity
    if (depth !== undefined) updateData.depth = depth
    if (reaction !== undefined) updateData.reaction = reaction
    if (flow !== undefined) updateData.flow = flow
    if (ownerId !== undefined) updateData.ownerId = ownerId || null

    const spirit = await prisma.spirit.update({
      where: { id },
      data: updateData,
      include: {
        template: true,
        owner: true,
      },
    })

    return NextResponse.json(spirit)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to update spirit' },
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
    await prisma.spirit.delete({
      where: { id },
    })

    return NextResponse.json({ success: true })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to delete spirit' },
      { status: 500 }
    )
  }
}
