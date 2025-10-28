import { z } from 'zod';
import { createRoute } from '@hono/zod-openapi';

const ordenSchema = z.object({
  OrdenId: z.number(),
  ClienteId: z.number(),
  Fecha: z.string().datetime(),
  Canal: z.string(),
  Moneda: z.string(),
  Total: z.string(),
});

const ordenDetalleSchema = z.object({
  OrdenDetalleId: z.number(),
  OrdenId: z.number(),
  ProductoId: z.number(),
  Cantidad: z.number(),
  PrecioUnit: z.string(),
  DescuentoPct: z.string().nullable(),
  producto: z.object({
    ProductoId: z.number(),
    SKU: z.string(),
    Nombre: z.string(),
    Categoria: z.string(),
  }).optional(),
});

const clienteSchema = z.object({
  ClienteId: z.number(),
  Nombre: z.string(),
  Email: z.string().nullable(),
  Genero: z.string().nullable(),
  Pais: z.string(),
  FechaRegistro: z.string().datetime(),
});

const ordenWithRelationsSchema = ordenSchema.extend({
  cliente: clienteSchema.optional(),
  detalles: z.array(ordenDetalleSchema).optional(),
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
      schema: { type: 'integer' },
    },
    {
      name: 'canal',
      in: 'query',
      required: false,
      schema: { type: 'string' },
    },
    {
      name: 'moneda',
      in: 'query',
      required: false,
      schema: { type: 'string' },
    },
    {
      name: 'fechaDesde',
      in: 'query',
      required: false,
      schema: { type: 'string', format: 'date-time' },
    },
    {
      name: 'fechaHasta',
      in: 'query',
      required: false,
      schema: { type: 'string', format: 'date-time' },
    },
    {
      name: 'sortBy',
      in: 'query',
      required: false,
      schema: { type: 'string' },
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
  },
});
