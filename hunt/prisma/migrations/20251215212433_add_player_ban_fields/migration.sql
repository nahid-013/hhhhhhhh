-- AlterTable
ALTER TABLE "Player" ADD COLUMN     "banReason" TEXT,
ADD COLUMN     "bannedAt" TIMESTAMP(3),
ADD COLUMN     "isBanned" BOOLEAN NOT NULL DEFAULT false;
