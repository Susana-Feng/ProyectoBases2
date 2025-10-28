import { z } from 'zod';
import { createRoute } from '@hono/zod-openapi';

const ordenDetalleSchema = z.object({
  OrdenDetalleId: z.number(),
  OrdenId: z.number(),
  ProductoId: z.number(),
  Cantidad: z.number(),
  PrecioUnit: z.string(),
  DescuentoPct: z.string().nullable(),
});

const ordenSchema = z.object({
  OrdenId: z.number(),
  ClienteId: z.number(),
  Fecha: z.string().datetime(),
  Canal: z.string(),
  Moneda: z.string(),
  Total: z.string(),
});

const productoSchema = z.object({
  ProductoId: z.number(),
  SKU: z.string(),
  Nombre: z.string(),
  Categoria: z.string(),
});

const ordenDetalleWithRelationsSchema = ordenDetalleSchema.extend({
  orden: ordenSchema.optional(),
  producto: productoSchema.optional(),
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
      schema: { type: 'integer', description: 'Minimum quantity (>= cantidadMin)' },
    },
    {
      name: 'cantidadMax',
      in: 'query',
      required: false,
      schema: { type: 'integer', description: 'Maximum quantity (<= cantidadMax)' },
    },
    {
      name: 'cantidadGt',
      in: 'query',
      required: false,
      schema: { type: 'integer', description: 'Quantity greater than (> cantidadGt)' },
    },
    {
      name: 'cantidadLt',
      in: 'query',
      required: false,
      schema: { type: 'integer', description: 'Quantity less than (< cantidadLt)' },
    },
    {
      name: 'cantidadEq',
      in: 'query',
      required: false,
      schema: { type: 'integer', description: 'Exact quantity (= cantidadEq)' },
    },
    {
      name: 'precioUnitMin',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Minimum unit price (>= precioUnitMin)' },
    },
    {
      name: 'precioUnitMax',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Maximum unit price (<= precioUnitMax)' },
    },
    {
      name: 'precioUnitGt',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Unit price greater than (> precioUnitGt)' },
    },
    {
      name: 'precioUnitLt',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Unit price less than (< precioUnitLt)' },
    },
    {
      name: 'precioUnitEq',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Exact unit price (= precioUnitEq)' },
    },
    {
      name: 'descuentoMin',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Minimum discount percentage (>= descuentoMin)' },
    },
    {
      name: 'descuentoMax',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Maximum discount percentage (<= descuentoMax)' },
    },
    {
      name: 'descuentoGt',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Discount percentage greater than (> descuentoGt)' },
    },
    {
      name: 'descuentoLt',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Discount percentage less than (< descuentoLt)' },
    },
    {
      name: 'descuentoEq',
      in: 'query',
      required: false,
      schema: { type: 'number', description: 'Exact discount percentage (= descuentoEq)' },
    },
    {
      name: 'sortBy',
      in: 'query',
      required: false,
      schema: { type: 'string', description: 'Sort field: Cantidad, PrecioUnit, DescuentoPct, OrdenDetalleId' },
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
