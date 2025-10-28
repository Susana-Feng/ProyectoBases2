import { z } from 'zod';
import { createRoute } from '@hono/zod-openapi';

const ordenSchema = z.object({
  id: z.number(),
  cliente_id: z.number(),
  fecha: z.string(),
  canal: z.string(),
  moneda: z.string(),
  total: z.string(),
});

const ordenWithRelationsSchema = ordenSchema.extend({
  cliente: z.object({
    id: z.number(),
    nombre: z.string(),
    correo: z.string().nullable(),
    genero: z.string(),
    pais: z.string(),
    created_at: z.string(),
  }).optional(),
  detalles: z.array(z.object({
    id: z.number(),
    orden_id: z.number(),
    producto_id: z.number(),
    cantidad: z.number(),
    precio_unit: z.string(),
    producto: z.object({
      id: z.number(),
      codigo_alt: z.string(),
      nombre: z.string(),
      categoria: z.string(),
    }).optional(),
  })).optional(),
});

const paginationMetadataSchema = z.object({
  page: z.number(),
  limit: z.number(),
  total: z.number(),
  totalPages: z.number(),
});

const errorResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  error: z.string().optional(),
});

export const listOrdenesRoute = createRoute({
  method: 'get',
  path: '/',
  tags: ['Data'],
  parameters: [
    {
      name: 'page',
      in: 'query',
      required: false,
      schema: { type: 'integer', minimum: 1, default: 1 },
    },
    {
      name: 'limit',
      in: 'query',
      required: false,
      schema: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
    },
    {
      name: 'clienteId',
      in: 'query',
      required: false,
      schema: { type: 'integer', description: 'Filter by cliente ID' },
    },
    {
      name: 'canal',
      in: 'query',
      required: false,
      schema: { type: 'string', description: 'Partial search by channel' },
    },
    {
      name: 'canalExact',
      in: 'query',
      required: false,
      schema: { type: 'string', enum: ['true', 'false'], description: 'Exact match for canal (default: false for partial)' },
    },
    {
      name: 'moneda',
      in: 'query',
      required: false,
      schema: { type: 'string', description: 'Filter by currency' },
    },
    {
      name: 'fechaDesde',
      in: 'query',
      required: false,
      schema: { type: 'string', description: 'Filter orders from this date onwards (YYYY-MM-DD HH:MM:SS)' },
    },
    {
      name: 'fechaHasta',
      in: 'query',
      required: false,
      schema: { type: 'string', description: 'Filter orders until this date (YYYY-MM-DD HH:MM:SS)' },
    },
    {
      name: 'totalMin',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Filter total >= X' },
    },
    {
      name: 'totalMax',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Filter total <= X' },
    },
    {
      name: 'totalGt',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Filter total > X' },
    },
    {
      name: 'totalLt',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Filter total < X' },
    },
    {
      name: 'totalEq',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Filter total = X' },
    },
    {
      name: 'sortBy',
      in: 'query',
      required: false,
      schema: { type: 'string', description: 'Sort field: fecha, canal, moneda, total, id' },
    },
    {
      name: 'sortOrder',
      in: 'query',
      required: false,
      schema: { type: 'string', enum: ['asc', 'desc'] },
    },
  ],
  responses: {
    200: {
      description: 'List of ordenes',
      content: {
        'application/json': {
          schema: z.object({
            success: z.boolean(),
            data: z.array(ordenSchema),
            pagination: paginationMetadataSchema,
          }),
        },
      },
    },
    400: {
      description: 'Invalid query parameters',
      content: {
        'application/json': {
          schema: errorResponseSchema,
        },
      },
    },
    500: {
      description: 'Internal server error',
      content: {
        'application/json': {
          schema: errorResponseSchema,
        },
      },
    },
  },
});

export const getOrdenRoute = createRoute({
  method: 'get',
  path: '/:id',
  tags: ['Data'],
  parameters: [
    {
      name: 'id',
      in: 'path',
      required: true,
      schema: { type: 'integer' },
    },
    {
      name: 'include',
      in: 'query',
      required: false,
      schema: { type: 'string', description: 'Comma-separated relations: cliente,detalles' },
    },
  ],
  responses: {
    200: {
      description: 'Orden by ID',
      content: {
        'application/json': {
          schema: z.object({
            success: z.boolean(),
            data: ordenWithRelationsSchema,
          }),
        },
      },
    },
    400: {
      description: 'Invalid orden ID',
      content: {
        'application/json': {
          schema: errorResponseSchema,
        },
      },
    },
    404: {
      description: 'Orden not found',
      content: {
        'application/json': {
          schema: z.object({
            success: z.boolean(),
            message: z.string(),
          }),
        },
      },
    },
    500: {
      description: 'Internal server error',
      content: {
        'application/json': {
          schema: errorResponseSchema,
        },
      },
    },
  },
});
