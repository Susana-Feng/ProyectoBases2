import { z } from 'zod';

// Base pagination schema
const basePaginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).default('asc').optional(),
});

// Cliente query schema - Adaptado para MySQL
export const clienteQuerySchema = basePaginationSchema.extend({
  nombre: z.string().optional(),
  nombreExact: z.enum(['true', 'false']).optional(),
  correo: z.string().optional(),
  correoExact: z.enum(['true', 'false']).optional(),
  pais: z.string().optional(),
  paisExact: z.enum(['true', 'false']).optional(),
  genero: z.enum(['M', 'F', 'X']).optional(),
  createdAtDesde: z.string().optional(), // YYYY-MM-DD
  createdAtHasta: z.string().optional(), // YYYY-MM-DD
  include: z.string().optional(), // 'ordenes'
});

// Producto query schema - Adaptado para MySQL
export const productoQuerySchema = basePaginationSchema.extend({
  nombre: z.string().optional(),
  nombreExact: z.enum(['true', 'false']).optional(),
  codigoAlt: z.string().optional(),
  codigoAltExact: z.enum(['true', 'false']).optional(),
  categoria: z.string().optional(),
  categoriaExact: z.enum(['true', 'false']).optional(),
  include: z.string().optional(), // 'ordenDetalles'
});

// Orden query schema - Adaptado para MySQL
export const ordenQuerySchema = basePaginationSchema.extend({
  clienteId: z.coerce.number().int().optional(),
  canal: z.string().optional(),
  canalExact: z.enum(['true', 'false']).optional(),
  moneda: z.string().optional(),
  fechaDesde: z.string().optional(), // YYYY-MM-DD HH:MM:SS
  fechaHasta: z.string().optional(), // YYYY-MM-DD HH:MM:SS
  totalMin: z.coerce.number().optional(),
  totalMax: z.coerce.number().optional(),
  totalGt: z.coerce.number().optional(),
  totalLt: z.coerce.number().optional(),
  totalEq: z.coerce.number().optional(),
  include: z.string().optional(), // 'cliente,detalles'
});

// OrdenDetalle query schema - Adaptado para MySQL
export const ordenDetalleQuerySchema = basePaginationSchema.extend({
  ordenId: z.coerce.number().int().optional(),
  productoId: z.coerce.number().int().optional(),
  cantidadMin: z.coerce.number().int().optional(),
  cantidadMax: z.coerce.number().int().optional(),
  cantidadGt: z.coerce.number().int().optional(),
  cantidadLt: z.coerce.number().int().optional(),
  cantidadEq: z.coerce.number().int().optional(),
  precioUnitMin: z.coerce.number().optional(),
  precioUnitMax: z.coerce.number().optional(),
  precioUnitGt: z.coerce.number().optional(),
  precioUnitLt: z.coerce.number().optional(),
  precioUnitEq: z.coerce.number().optional(),
  include: z.string().optional(), // 'orden,producto'
});

export type ClienteQuery = z.infer<typeof clienteQuerySchema>;
export type ProductoQuery = z.infer<typeof productoQuerySchema>;
export type OrdenQuery = z.infer<typeof ordenQuerySchema>;
export type OrdenDetalleQuery = z.infer<typeof ordenDetalleQuerySchema>;
