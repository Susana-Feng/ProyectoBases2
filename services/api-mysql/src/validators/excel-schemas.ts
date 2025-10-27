import { z } from 'zod';

// Schema for Cliente sheet
export const clienteSchema = z.object({
  nombre: z.string().min(1).max(120),
  correo: z.string().email().max(150).optional(),
  genero: z.enum(['M', 'F', 'X']).default('M'), // DEFAULT 'M' in MySQL
  pais: z.string().min(1).max(60),
  created_at: z.union([z.date(), z.string()]).optional(), // Will use current date if not provided
});

// Schema for Producto sheet
export const productoSchema = z.object({
  codigo_alt: z.string().min(1).max(64),
  nombre: z.string().min(1).max(150),
  categoria: z.string().min(1).max(80),
});

// Schema for Orden sheet
export const ordenSchema = z.object({
  correo: z.string().email(), // For finding cliente
  fecha: z.union([z.date(), z.string()]).optional(), // Will use current datetime if not provided
  canal: z.string().min(1).max(20), // Canal is free text, not controlled (heterogeneidad)
  moneda: z.enum(['USD', 'CRC']).default('USD'), // ENUM in MySQL, default to USD if not provided
  total: z.union([z.number(), z.string()]).transform((val) => {
    // Handle both number and string (with or without commas)
    if (typeof val === 'number') return String(val);
    return val;
  }),
});

// Schema for OrdenDetalle sheet
export const ordenDetalleSchema = z.object({
  OrdenIndex: z.number().int().positive(),
  codigo_alt: z.string().min(1).max(64),
  cantidad: z.number().int().positive(),
  precio_unit: z.union([z.number(), z.string()]).transform((val) => {
    // Handle both number and string (with or without commas)
    if (typeof val === 'number') return String(val);
    return val;
  }),
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
