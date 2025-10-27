import { describe, test, expect } from 'bun:test';
import {
  clienteSchema,
  productoSchema,
  ordenSchema,
  ordenDetalleSchema,
  excelDataSchema,
} from '../excel-schemas';

describe('Excel Schemas Validation', () => {
  describe('clienteSchema', () => {
    test('should validate valid cliente data', () => {
      const validData = {
        Nombre: 'Juan Pérez',
        Email: 'juan@example.com',
        Genero: 'Masculino',
        Pais: 'Costa Rica',
      };

      const result = clienteSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should accept cliente without optional fields', () => {
      const validData = {
        Nombre: 'Juan Pérez',
        Pais: 'Costa Rica',
      };

      const result = clienteSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should reject invalid email', () => {
      const invalidData = {
        Nombre: 'Juan Pérez',
        Email: 'not-an-email',
        Pais: 'Costa Rica',
      };

      const result = clienteSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should reject invalid Genero', () => {
      const invalidData = {
        Nombre: 'Juan Pérez',
        Genero: 'Invalid',
        Pais: 'Costa Rica',
      };

      const result = clienteSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should reject missing required fields', () => {
      const invalidData = {
        Email: 'juan@example.com',
      };

      const result = clienteSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });
  });

  describe('productoSchema', () => {
    test('should validate valid producto data', () => {
      const validData = {
        SKU: 'PROD-001',
        Nombre: 'Laptop Dell',
        Categoria: 'Electrónica',
      };

      const result = productoSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should reject missing required fields', () => {
      const invalidData = {
        SKU: 'PROD-001',
      };

      const result = productoSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should reject empty SKU', () => {
      const invalidData = {
        SKU: '',
        Nombre: 'Product',
        Categoria: 'Category',
      };

      const result = productoSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });
  });

  describe('ordenSchema', () => {
    test('should validate valid orden data', () => {
      const validData = {
        Email: 'customer@example.com',
        Canal: 'WEB',
        Total: 1500.50,
      };

      const result = ordenSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should accept valid Canal values', () => {
      const canales = ['WEB', 'TIENDA', 'APP'];

      canales.forEach((canal) => {
        const data = {
          Email: 'test@example.com',
          Canal: canal,
          Total: 100,
        };
        const result = ordenSchema.safeParse(data);
        expect(result.success).toBe(true);
      });
    });

    test('should reject invalid Canal', () => {
      const invalidData = {
        Email: 'test@example.com',
        Canal: 'INVALID',
        Total: 100,
      };

      const result = ordenSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should reject negative Total', () => {
      const invalidData = {
        Email: 'test@example.com',
        Canal: 'WEB',
        Total: -100,
      };

      const result = ordenSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should reject invalid email', () => {
      const invalidData = {
        Email: 'not-an-email',
        Canal: 'WEB',
        Total: 100,
      };

      const result = ordenSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should default Moneda to USD', () => {
      const data = {
        Email: 'test@example.com',
        Canal: 'WEB',
        Total: 100,
      };

      const result = ordenSchema.parse(data);
      expect(result.Moneda).toBe('USD');
    });
  });

  describe('ordenDetalleSchema', () => {
    test('should validate valid orden detalle data', () => {
      const validData = {
        OrdenIndex: 1,
        SKU: 'PROD-001',
        Cantidad: 5,
        PrecioUnit: 100.50,
      };

      const result = ordenDetalleSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should accept optional DescuentoPct', () => {
      const validData = {
        OrdenIndex: 1,
        SKU: 'PROD-001',
        Cantidad: 5,
        PrecioUnit: 100.50,
        DescuentoPct: 10,
      };

      const result = ordenDetalleSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should reject negative Cantidad', () => {
      const invalidData = {
        OrdenIndex: 1,
        SKU: 'PROD-001',
        Cantidad: -5,
        PrecioUnit: 100,
      };

      const result = ordenDetalleSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should reject DescuentoPct > 100', () => {
      const invalidData = {
        OrdenIndex: 1,
        SKU: 'PROD-001',
        Cantidad: 5,
        PrecioUnit: 100,
        DescuentoPct: 150,
      };

      const result = ordenDetalleSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should reject DescuentoPct < 0', () => {
      const invalidData = {
        OrdenIndex: 1,
        SKU: 'PROD-001',
        Cantidad: 5,
        PrecioUnit: 100,
        DescuentoPct: -10,
      };

      const result = ordenDetalleSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should reject zero OrdenIndex', () => {
      const invalidData = {
        OrdenIndex: 0,
        SKU: 'PROD-001',
        Cantidad: 5,
        PrecioUnit: 100,
      };

      const result = ordenDetalleSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });
  });

  describe('excelDataSchema', () => {
    test('should validate complete Excel data', () => {
      const validData = {
        Cliente: [
          {
            Nombre: 'Juan Pérez',
            Email: 'juan@example.com',
            Pais: 'Costa Rica',
          },
        ],
        Producto: [
          {
            SKU: 'PROD-001',
            Nombre: 'Laptop',
            Categoria: 'Electrónica',
          },
        ],
        Orden: [
          {
            Email: 'juan@example.com',
            Canal: 'WEB',
            Total: 1500,
          },
        ],
        OrdenDetalle: [
          {
            OrdenIndex: 1,
            SKU: 'PROD-001',
            Cantidad: 1,
            PrecioUnit: 1500,
          },
        ],
      };

      const result = excelDataSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should accept partial Excel data', () => {
      const validData = {
        Cliente: [
          {
            Nombre: 'Juan Pérez',
            Pais: 'Costa Rica',
          },
        ],
      };

      const result = excelDataSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should accept empty Excel data', () => {
      const validData = {};

      const result = excelDataSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });
  });
});

