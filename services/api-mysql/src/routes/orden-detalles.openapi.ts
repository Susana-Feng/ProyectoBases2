import { z } from 'zod';
import { createRoute } from '@hono/zod-openapi';

const ordenDetalleSchema = z.object({
  id: z.number(),
  orden_id: z.number(),
  producto_id: z.number(),
  cantidad: z.number(),
  precio_unit: z.string(),
});

const ordenDetalleWithRelationsSchema = ordenDetalleSchema.extend({
  orden: z.object({
    id: z.number(),
    cliente_id: z.number(),
    fecha: z.string(),
    canal: z.string(),
    moneda: z.string(),
    total: z.string(),
  }).optional(),
  producto: z.object({
    id: z.number(),
    codigo_alt: z.string(),
    nombre: z.string(),
    categoria: z.string(),
  }).optional(),
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

export const listOrdenDetallesRoute = createRoute({
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
      name: 'ordenId',
      in: 'query',
      required: false,
      schema: { type: 'integer', description: 'Filter by order ID' },
    },
    {
      name: 'productoId',
      in: 'query',
      required: false,
      schema: { type: 'integer', description: 'Filter by product ID' },
    },
    {
      name: 'cantidadMin',
      in: 'query',
      required: false,
      schema: { type: 'integer', description: 'Filter cantidad >= X' },
    },
    {
      name: 'cantidadMax',
      in: 'query',
      required: false,
      schema: { type: 'integer', description: 'Filter cantidad <= X' },
    },
    {
      name: 'cantidadGt',
      in: 'query',
      required: false,
      schema: { type: 'integer', description: 'Filter cantidad > X' },
    },
    {
      name: 'cantidadLt',
      in: 'query',
      required: false,
      schema: { type: 'integer', description: 'Filter cantidad < X' },
    },
    {
      name: 'cantidadEq',
      in: 'query',
      required: false,
      schema: { type: 'integer', description: 'Filter cantidad = X' },
    },
    {
      name: 'precioUnitMin',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Filter precio_unit >= X' },
    },
    {
      name: 'precioUnitMax',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Filter precio_unit <= X' },
    },
    {
      name: 'precioUnitGt',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Filter precio_unit > X' },
    },
    {
      name: 'precioUnitLt',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Filter precio_unit < X' },
    },
    {
      name: 'precioUnitEq',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Filter precio_unit = X' },
    },
    {
      name: 'sortBy',
      in: 'query',
      required: false,
      schema: { type: 'string', description: 'Sort field: cantidad, precio_unit, id' },
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
      description: 'List of orden detalles',
      content: {
        'application/json': {
          schema: z.object({
            success: z.boolean(),
            data: z.array(ordenDetalleSchema),
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

export const getOrdenDetalleRoute = createRoute({
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
      schema: { type: 'string', description: 'Comma-separated relations: orden,producto' },
    },
  ],
  responses: {
    200: {
      description: 'Orden detalle by ID',
      content: {
        'application/json': {
          schema: z.object({
            success: z.boolean(),
            data: ordenDetalleWithRelationsSchema,
          }),
        },
      },
    },
    400: {
      description: 'Invalid orden detalle ID',
      content: {
        'application/json': {
          schema: errorResponseSchema,
        },
      },
    },
    404: {
      description: 'Orden detalle not found',
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
