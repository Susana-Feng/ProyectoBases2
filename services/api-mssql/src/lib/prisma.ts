import { PrismaClient } from '@prisma/client';
import { PrismaMssql } from '@prisma/adapter-mssql';

// Get DATABASE_URL from environment (Bun loads .env automatically)
const databaseUrl = process.env.DATABASE_URL || Bun.env.DATABASE_URL;

if (!databaseUrl) {
  throw new Error('DATABASE_URL environment variable is not set');
}

// Create MSSQL adapter using connection string directly
const adapter = new PrismaMssql(databaseUrl);

// Create Prisma Client with MSSQL adapter
export const prisma = new PrismaClient({ adapter });

// Graceful shutdown
process.on('beforeExit', async () => {
  await prisma.$disconnect();
});

