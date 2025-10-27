import { PrismaClient } from '@prisma/client';

// Get DATABASE_URL from environment (Bun loads .env automatically)
const databaseUrl = process.env.DATABASE_URL || Bun.env.DATABASE_URL;

if (!databaseUrl) {
  throw new Error('DATABASE_URL environment variable is not set');
}

// Create Prisma Client for MySQL (no adapter needed)
export const prisma = new PrismaClient();

// Graceful shutdown
process.on('beforeExit', async () => {
  await prisma.$disconnect();
});
