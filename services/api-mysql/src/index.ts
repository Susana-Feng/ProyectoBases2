import { OpenAPIHono } from '@hono/zod-openapi';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { swaggerUI } from '@hono/swagger-ui';
import uploadRoutes from './routes/upload';
import { rootRoute, healthRoute } from './routes/health.openapi';

// Create OpenAPI Hono app
const app = new OpenAPIHono();

// Middleware
app.use('*', logger());
app.use('*', cors());

// Health check endpoints
app.openapi(rootRoute, (c) => {
  return c.json({
    success: true,
    message: 'API Excel to MSSQL is running',
    version: '1.0.0',
  });
});

app.openapi(healthRoute, (c) => {
  return c.json({
    success: true,
    status: 'healthy',
    timestamp: new Date().toISOString(),
  });
});

// Routes
app.route('/upload', uploadRoutes);

// OpenAPI documentation
app.doc('/openapi.json', {
  openapi: '3.1.0',
  info: {
    title: 'Excel to MySQL API',
    version: '1.0.0',
    description: `API para procesar archivos Excel e insertarlos en MySQL usando Prisma ORM.`,
  },
  servers: [
    {
      url: 'http://localhost:3001',
      description: 'MySQL Development server',
    },
  ],
  tags: [
    {
      name: 'Upload',
      description: 'Endpoints para subir y procesar archivos Excel',
    },
    {
      name: 'Health',
      description: 'Endpoints de salud y estado del servicio',
    },
  ],
});

// Swagger UI (handle both /docs and /docs/)
app.get('/docs', swaggerUI({ url: '/openapi.json' }));
app.get('/docs/', swaggerUI({ url: '/openapi.json' }));

// 404 handler
app.notFound((c) => {
  return c.json(
    {
      success: false,
      message: 'Route not found',
    },
    404
  );
});

// Error handler
app.onError((err, c) => {
  console.error('Unhandled error:', err);
  
  return c.json(
    {
      success: false,
      message: 'Internal server error',
      error: err.message,
    },
    500
  );
});

// Export app for testing
export { app };

// Start server
const port = parseInt(Bun.env.PORT || process.env.PORT || '3001');

console.log(`🚀 Server starting on port ${port}...`);

export default {
  port,
  fetch: app.fetch,
};

