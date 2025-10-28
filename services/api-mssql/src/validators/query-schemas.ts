import { z } from 'zod';

// Base pagination schema
const basePaginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).default('asc').optional(),
});

// Numeric filter operators schema
const numericFilterSchema = z.object({
  gt: z.coerce.number().optional(),   // greater than
  gte: z.coerce.number().optional(),  // greater than or equal
  lt: z.coerce.number().optional(),   // less than
  lte: z.coerce.number().optional(),  // less than or equal
  eq: z.coerce.number().optional(),   // equal
  ne: z.coerce.number().optional(),   // not equal
}).partial().optional();

// Date filter operators schema
const dateFilterSchema = z.object({
  gt: z.string().datetime({ offset: true }).optional(),
  gte: z.string().datetime({ offset: true }).optional(),
  lt: z.string().datetime({ offset: true }).optional(),
  lte: z.string().datetime({ offset: true }).optional(),
}).partial().optional();

// Cliente query schema - MEJORADO
export const clienteQuerySchema = basePaginationSchema.extend({
  nombre: z.string().optional(),
  nombreExact: z.enum(['true', 'false']).optional(), // Exact match instead of contains
  email: z.string().optional(),
  emailExact: z.enum(['true', 'false']).optional(),
  pais: z.string().optional(),
  paisExact: z.enum(['true', 'false']).optional(),
  genero: z.string().optional(),
  fechaRegistroDesde: z.string().datetime({ offset: true }).optional(),
  fechaRegistroHasta: z.string().datetime({ offset: true }).optional(),
  include: z.string().optional(), // 'ordenes'
});

// Producto query schema - MEJORADO
export const productoQuerySchema = basePaginationSchema.extend({
  nombre: z.string().optional(),
  nombreExact: z.enum(['true', 'false']).optional(),
  sku: z.string().optional(),
  skuExact: z.enum(['true', 'false']).optional(),
  categoria: z.string().optional(),
  categoriaExact: z.enum(['true', 'false']).optional(),
  include: z.string().optional(), // 'ordenDetalles'
});

// Orden query schema - MEJORADO
export const ordenQuerySchema = basePaginationSchema.extend({
  clienteId: z.coerce.number().int().optional(),
  canal: z.string().optional(),
  canalExact: z.enum(['true', 'false']).optional(),
  moneda: z.string().optional(),
  fechaDesde: z.string().datetime({ offset: true }).optional(),
  fechaHasta: z.string().datetime({ offset: true }).optional(),
  totalMin: z.coerce.number().optional(),    // Total >= X
  totalMax: z.coerce.number().optional(),    // Total <= X
  totalGt: z.coerce.number().optional(),     // Total > X
  totalLt: z.coerce.number().optional(),     // Total < X
  totalEq: z.coerce.number().optional(),     // Total = X
  include: z.string().optional(), // 'cliente,detalles'
});

// OrdenDetalle query schema - MEJORADO
export const ordenDetalleQuerySchema = basePaginationSchema.extend({
  ordenId: z.coerce.number().int().optional(),
  productoId: z.coerce.number().int().optional(),
  cantidadMin: z.coerce.number().int().optional(),    // Cantidad >= X
  cantidadMax: z.coerce.number().int().optional(),    // Cantidad <= X
  cantidadGt: z.coerce.number().int().optional(),     // Cantidad > X
  cantidadLt: z.coerce.number().int().optional(),     // Cantidad < X
  cantidadEq: z.coerce.number().int().optional(),     // Cantidad = X
  precioUnitMin: z.coerce.number().optional(),        // PrecioUnit >= X
  precioUnitMax: z.coerce.number().optional(),        // PrecioUnit <= X
  precioUnitGt: z.coerce.number().optional(),         // PrecioUnit > X
  precioUnitLt: z.coerce.number().optional(),         // PrecioUnit < X
  precioUnitEq: z.coerce.number().optional(),         // PrecioUnit = X
  descuentoMin: z.coerce.number().optional(),         // DescuentoPct >= X
  descuentoMax: z.coerce.number().optional(),         // DescuentoPct <= X
  descuentoGt: z.coerce.number().optional(),          // DescuentoPct > X
  descuentoLt: z.coerce.number().optional(),          // DescuentoPct < X
  descuentoEq: z.coerce.number().optional(),          // DescuentoPct = X
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
