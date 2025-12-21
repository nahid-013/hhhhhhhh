# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HUNT is a Web3 game Mini App for Telegram on the TON blockchain. Players collect, develop, synthesize, and trade energy creatures called Spiriks that exist as NFTs.

## Repository Structure

```
hhhhhhhh/
├── hunt/          # Next.js main app (admin panel, API)
├── games/         # Game service (Node.js + Socket.io + Phaser.js)
├── docker-compose.yml        # Production Docker config
├── docker-compose.dev.yml    # Development Docker config
└── Makefile                  # Common commands
```

## Common Commands

```bash
# Install dependencies
make install

# Development (all services with Docker)
make dev              # Start all services
make dev-up           # Start only PostgreSQL
make dev-down         # Stop dev environment

# Production
make build            # Build Docker images
make up               # Start production services
make down             # Stop production services

# Database
make migrate          # Run Prisma migrations
make db-push          # Sync schema without migrations

# Logs & Status
make logs             # View all logs
make ps               # Container status
```

### Hunt (Next.js) - Port 3000

```bash
cd hunt
npm run dev           # Start dev server
npm run build         # Production build
npm run lint          # ESLint
npm run db:generate   # Generate Prisma client
npm run db:migrate    # Run migrations
npm run db:studio     # Open Prisma Studio
```

### Games Service - Port 9000

```bash
cd games
npm run dev           # Start with tsx watch
npm run build         # Compile TypeScript
npm run start         # Start production server
```

## Architecture

### Tech Stack
- **Hunt**: Next.js 16, App Router, Tailwind CSS 4, Prisma ORM
- **Games**: Node.js, Express, Socket.io, Phaser.js 3
- **Database**: PostgreSQL 16
- **Containerization**: Docker Compose

### Data Models (hunt/prisma/schema.prisma)
- **Player**: User with Telegram ID, wallet, ban status
- **SpiritTemplate**: Base template with element, rarity, stats
- **Spirit**: Instance with owner, level, XP, current stats
- **PlayerSpirit**: Player-Spirit assignment with slot

### Enums
- **Element**: AIR, WATER, EARTH, LIGHTNING, FOREST
- **Rarity**: COMMON, RARE, EPIC, LEGENDARY, MYTHIC
- **Spirit Stats**: maneuver, impulse, fluidity, depth, reaction, flow

### Games Service Structure

```
games/src/
├── server.ts              # Express + Socket.io entry
├── config/index.ts        # Configuration
├── socket/
│   ├── index.ts           # Socket.io setup
│   ├── matchmaking.ts     # Queue & room management
│   └── game-events.ts     # Input handlers
├── games/flow-flight/
│   ├── FlowFlightRoom.ts  # Game room logic
│   ├── obstacles.ts       # Obstacle generation
│   └── scoring.ts         # Rewards calculation
└── services/
    ├── player.service.ts  # DB operations
    └── rewards.service.ts # Apply rewards
```

### Socket.io Events

**Client → Server:**
- `join-queue` - Join matchmaking queue
- `leave-queue` - Leave queue
- `player-input` - Movement input (up/down/none)
- `player-ready` - Ready signal

**Server → Client:**
- `queue-status` - Queue position
- `match-found` - Match created
- `game-countdown` - Countdown (3, 2, 1)
- `game-start` - Game started with seed
- `game-state` - Player positions (60 FPS)
- `player-eliminated` - Player collision
- `game-end` - Results and rewards

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hunt

# Ports
APP_PORT=3000
GAMES_PORT=9000

# Docker defaults
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=hunt
```

## Flow Flight Game

**Mechanics:**
- 3 players per match
- Runner-style obstacle avoidance
- Swipe up/down to move vertically
- Distance-based scoring
- Spirit stats affect gameplay:
  - `maneuver` → turn speed
  - `flow` → base speed
  - `reaction` → input delay

**Rewards by place:**
- 1st: 250+ Lumens, 30 XP, 5% chance 0.1 TON, 10% Pulse Capsule
- 2nd: 150+ Lumens, 20 XP, 2% chance 0.05 TON
- 3rd: 50+ Lumens, 10 XP
