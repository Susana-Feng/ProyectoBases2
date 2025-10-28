import { createRoute, z } from '@hono/zod-openapi';

// Schema for health check response
const HealthResponseSchema = z.object({
  success: z.boolean().openapi({ example: true }),
  status: z.string().openapi({ example: 'healthy' }),
  timestamp: z.string().openapi({ example: '2024-01-20T12:00:00.000Z' }),
}).openapi('HealthResponse');

// Schema for root response
const RootResponseSchema = z.object({
  success: z.boolean().openapi({ example: true }),
  message: z.string().openapi({ example: 'API Excel to MySQL is running' }),
  version: z.string().openapi({ example: '1.0.0' }),
}).openapi('RootResponse');

// Route for root endpoint
export const rootRoute = createRoute({
  method: 'get',
  path: '/',
  tags: ['Health'],
  summary: 'API root',
  description: 'Returns basic API information',
  responses: {
    200: {
      content: {
        'application/json': {
          schema: RootResponseSchema,
        },
      },
      description: 'API information',
    },
  },
});

// Route for health check
export const healthRoute = createRoute({
  method: 'get',
  path: '/health',
  tags: ['Health'],
  summary: 'Health check',
  description: 'Returns the health status of the API',
  responses: {
    200: {
      content: {
        'application/json': {
          schema: HealthResponseSchema,
        },
      },
      description: 'API health status',
    },
  },
});


