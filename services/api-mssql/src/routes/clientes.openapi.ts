import { z } from 'zod';
import { createRoute } from '@hono/zod-openapi';

const clienteSchema = z.object({
  ClienteId: z.number(),
  Nombre: z.string(),
  Email: z.string().nullable(),
  Genero: z.string().nullable(),
  Pais: z.string(),
  FechaRegistro: z.string().datetime(),
});

const clienteWithOrdenesSchema = clienteSchema.extend({
  ordenes: z.array(z.object({
    OrdenId: z.number(),
    ClienteId: z.number(),
    Fecha: z.string().datetime(),
    Canal: z.string(),
    Moneda: z.string(),
    Total: z.string(), // Decimal as string
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

export const listClientesRoute = createRoute({
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
      schema: { type: 'string' },
    },
    {
      name: 'email',
      in: 'query',
      required: false,
      schema: { type: 'string' },
    },
    {
      name: 'pais',
      in: 'query',
      required: false,
      schema: { type: 'string' },
    },
    {
      name: 'genero',
      in: 'query',
      required: false,
      schema: { type: 'string' },
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
      description: 'List of clientes',
      content: {
        'application/json': {
          schema: z.object({
            success: z.boolean(),
            data: z.array(clienteSchema),
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

export const getClienteRoute = createRoute({
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
      schema: { type: 'string', description: 'Comma-separated relations: ordenes' },
    },
  ],
  responses: {
    200: {
      description: 'Cliente by ID',
      content: {
        'application/json': {
          schema: z.object({
            success: z.boolean(),
            data: clienteWithOrdenesSchema,
          }),
        },
      },
    },
    400: {
      description: 'Invalid cliente ID',
      content: {
        'application/json': {
          schema: errorResponseSchema,
        },
      },
    },
    404: {
      description: 'Cliente not found',
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
