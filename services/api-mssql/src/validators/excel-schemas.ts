import { z } from 'zod';

// Schema for Cliente sheet
export const clienteSchema = z.object({
  Nombre: z.string().min(1).max(120),
  Email: z.string().email().max(150).optional(),
  Genero: z.enum(['Masculino', 'Femenino']).optional(),
  Pais: z.string().min(1).max(60),
  FechaRegistro: z.union([z.date(), z.string()]).optional(),
});

// Schema for Producto sheet
export const productoSchema = z.object({
  SKU: z.string().min(1).max(40),
  Nombre: z.string().min(1).max(150),
  Categoria: z.string().min(1).max(80),
});

// Schema for Orden sheet
export const ordenSchema = z.object({
  Email: z.string().email(),
  Fecha: z.union([z.date(), z.string()]).optional(),
  Canal: z.enum(['WEB', 'TIENDA', 'APP']),
  Moneda: z.string().length(3).optional().default('USD'),
  Total: z.number().positive(),
});

// Schema for OrdenDetalle sheet
export const ordenDetalleSchema = z.object({
  OrdenIndex: z.number().int().positive(),
  SKU: z.string().min(1).max(40),
  Cantidad: z.number().int().positive(),
  PrecioUnit: z.number().positive(),
  DescuentoPct: z.number().min(0).max(100).nullable().optional(),
});

// Schema for the complete Excel data
export const excelDataSchema = z.object({
  Cliente: z.array(clienteSchema).optional(),
  Producto: z.array(productoSchema).optional(),
  Orden: z.array(ordenSchema).optional(),
  OrdenDetalle: z.array(ordenDetalleSchema).optional(),
});

export type ClienteInput = z.infer<typeof clienteSchema>;
export type ProductoInput = z.infer<typeof productoSchema>;
export type OrdenInput = z.infer<typeof ordenSchema>;
export type OrdenDetalleInput = z.infer<typeof ordenDetalleSchema>;
export type ExcelDataInput = z.infer<typeof excelDataSchema>;

