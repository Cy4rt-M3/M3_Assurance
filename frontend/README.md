# Dashboard Frontend

## Prerequisites

- [Bun](https://bun.sh) >= 1.x

## Setup

```bash
# Install dependencies
bun install

# Initialize the database
cp .env.example .env
bun run db:generate
bun run db:push

# Start dev server
bun run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Scripts

| Command | Description |
|---------|-------------|
| `bun run dev` | Start dev server on port 3000 |
| `bun run build` | Build for production |
| `bun run start` | Start production server |
| `bun run lint` | Run ESLint |
| `bun run db:generate` | Generate Prisma client |
| `bun run db:push` | Push schema to database |
| `bun run db:migrate` | Run Prisma migrations |
| `bun run db:reset` | Reset database |
