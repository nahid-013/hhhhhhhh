-- CreateEnum
CREATE TYPE "Element" AS ENUM ('AIR', 'WATER', 'EARTH', 'LIGHTNING', 'FOREST');

-- CreateEnum
CREATE TYPE "Rarity" AS ENUM ('COMMON', 'RARE', 'EPIC', 'LEGENDARY', 'MYTHIC');

-- CreateTable
CREATE TABLE "Player" (
    "id" TEXT NOT NULL,
    "telegramId" TEXT,
    "walletAddress" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Player_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SpiritTemplate" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "element" "Element" NOT NULL,
    "rarity" "Rarity" NOT NULL,
    "generation" INTEGER NOT NULL DEFAULT 1,
    "baseManeuver" INTEGER NOT NULL,
    "baseImpulse" INTEGER NOT NULL,
    "baseFluidity" INTEGER NOT NULL,
    "baseDepth" INTEGER NOT NULL,
    "baseReaction" INTEGER NOT NULL,
    "baseFlow" INTEGER NOT NULL,
    "perk" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "SpiritTemplate_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Spirit" (
    "id" TEXT NOT NULL,
    "templateId" TEXT NOT NULL,
    "ownerId" TEXT,
    "level" INTEGER NOT NULL DEFAULT 1,
    "xp" INTEGER NOT NULL DEFAULT 0,
    "hunger" INTEGER NOT NULL DEFAULT 100,
    "energy" INTEGER NOT NULL DEFAULT 100,
    "maxEnergy" INTEGER NOT NULL DEFAULT 100,
    "maneuver" INTEGER NOT NULL,
    "impulse" INTEGER NOT NULL,
    "fluidity" INTEGER NOT NULL,
    "depth" INTEGER NOT NULL,
    "reaction" INTEGER NOT NULL,
    "flow" INTEGER NOT NULL,
    "nftTokenId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Spirit_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PlayerSpirit" (
    "id" TEXT NOT NULL,
    "playerId" TEXT NOT NULL,
    "spiritId" TEXT NOT NULL,
    "slotIndex" INTEGER,
    "isActive" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "PlayerSpirit_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Player_telegramId_key" ON "Player"("telegramId");

-- CreateIndex
CREATE INDEX "PlayerSpirit_playerId_idx" ON "PlayerSpirit"("playerId");

-- CreateIndex
CREATE INDEX "PlayerSpirit_spiritId_idx" ON "PlayerSpirit"("spiritId");

-- CreateIndex
CREATE UNIQUE INDEX "PlayerSpirit_playerId_spiritId_key" ON "PlayerSpirit"("playerId", "spiritId");

-- AddForeignKey
ALTER TABLE "Spirit" ADD CONSTRAINT "Spirit_templateId_fkey" FOREIGN KEY ("templateId") REFERENCES "SpiritTemplate"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Spirit" ADD CONSTRAINT "Spirit_ownerId_fkey" FOREIGN KEY ("ownerId") REFERENCES "Player"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PlayerSpirit" ADD CONSTRAINT "PlayerSpirit_playerId_fkey" FOREIGN KEY ("playerId") REFERENCES "Player"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PlayerSpirit" ADD CONSTRAINT "PlayerSpirit_spiritId_fkey" FOREIGN KEY ("spiritId") REFERENCES "Spirit"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
