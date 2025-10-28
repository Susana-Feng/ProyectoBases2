import { z } from 'zod';
import { createRoute } from '@hono/zod-openapi';

const productoSchema = z.object({
  ProductoId: z.number(),
  SKU: z.string(),
  Nombre: z.string(),
  Categoria: z.string(),
});

const productoWithDetallesSchema = productoSchema.extend({
  ordenDetalles: z.array(z.object({
    OrdenDetalleId: z.number(),
    OrdenId: z.number(),
    ProductoId: z.number(),
    Cantidad: z.number(),
    PrecioUnit: z.string(),
    DescuentoPct: z.string().nullable(),
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

export const listProductosRoute = createRoute({
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
      name: 'nombre',
      in: 'query',
      required: false,
      schema: { type: 'string', description: 'Partial search by product name' },
    },
    {
      name: 'nombreExact',
      in: 'query',
      required: false,
      schema: { type: 'string', enum: ['true', 'false'], description: 'Exact match for nombre (default: false for partial)' },
    },
    {
      name: 'sku',
      in: 'query',
      required: false,
      schema: { type: 'string', description: 'Partial search by SKU' },
    },
    {
      name: 'skuExact',
      in: 'query',
      required: false,
      schema: { type: 'string', enum: ['true', 'false'], description: 'Exact match for SKU (default: false for partial)' },
    },
    {
      name: 'categoria',
      in: 'query',
      required: false,
      schema: { type: 'string', description: 'Partial search by category' },
    },
    {
      name: 'categoriaExact',
      in: 'query',
      required: false,
      schema: { type: 'string', enum: ['true', 'false'], description: 'Exact match for categoria (default: false for partial)' },
    },
    {
      name: 'sortBy',
      in: 'query',
      required: false,
      schema: { type: 'string', description: 'Sort field: SKU, Nombre, Categoria, ProductoId' },
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
      description: 'List of productos',
      content: {
        'application/json': {
          schema: z.object({
            success: z.boolean(),
            data: z.array(productoSchema),
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

export const getProductoRoute = createRoute({
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
      schema: { type: 'string', description: 'Comma-separated relations: ordenDetalles' },
    },
  ],
  responses: {
    200: {
      description: 'Producto by ID',
      content: {
        'application/json': {
          schema: z.object({
            success: z.boolean(),
            data: productoWithDetallesSchema,
          }),
        },
      },
    },
    400: {
      description: 'Invalid producto ID',
      content: {
        'application/json': {
          schema: errorResponseSchema,
        },
      },
    },
    404: {
      description: 'Producto not found',
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
