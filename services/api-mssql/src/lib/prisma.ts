import { PrismaClient } from '@prisma/client';

// Create Prisma Client using built-in SQL Server driver
// DATABASE_URL is automatically loaded from .env by Bun
export const prisma = new PrismaClient();

// Graceful shutdown
process.on('beforeExit', async () => {
  await prisma.$disconnect();
});

