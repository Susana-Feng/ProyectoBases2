import { z } from 'zod';

// Base pagination schema
const basePaginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).default('asc').optional(),
});

// Cliente query schema
export const clienteQuerySchema = basePaginationSchema.extend({
  nombre: z.string().optional(),
  email: z.string().optional(), // Allow partial email search
  pais: z.string().optional(),
  genero: z.string().optional(),
  include: z.string().optional(), // 'ordenes'
});

// Producto query schema
export const productoQuerySchema = basePaginationSchema.extend({
  nombre: z.string().optional(),
  sku: z.string().optional(),
  categoria: z.string().optional(),
  include: z.string().optional(), // 'ordenDetalles'
});

// Orden query schema
export const ordenQuerySchema = basePaginationSchema.extend({
  clienteId: z.coerce.number().int().optional(),
  canal: z.string().optional(),
  moneda: z.string().optional(),
  fechaDesde: z.string().datetime({ offset: true }).optional(),
  fechaHasta: z.string().datetime({ offset: true }).optional(),
  include: z.string().optional(), // 'cliente,detalles'
});

// OrdenDetalle query schema
export const ordenDetalleQuerySchema = basePaginationSchema.extend({
  ordenId: z.coerce.number().int().optional(),
  productoId: z.coerce.number().int().optional(),
  include: z.string().optional(), // 'orden,producto'
});

// Schema for includes validation
export const includesSchema = z.object({
  include: z.string().optional(),
});

export type ClienteQuery = z.infer<typeof clienteQuerySchema>;
export type ProductoQuery = z.infer<typeof productoQuerySchema>;
export type OrdenQuery = z.infer<typeof ordenQuerySchema>;
export type OrdenDetalleQuery = z.infer<typeof ordenDetalleQuerySchema>;
