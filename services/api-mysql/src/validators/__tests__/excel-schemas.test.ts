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
        nombre: 'Juan Pérez',
        correo: 'juan@example.com',
        genero: 'M',
        pais: 'Costa Rica',
      };

      const result = clienteSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should accept cliente without optional fields', () => {
      const validData = {
        nombre: 'Juan Pérez',
        pais: 'Costa Rica',
      };

      const result = clienteSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should reject invalid email', () => {
      const invalidData = {
        nombre: 'Juan Pérez',
        correo: 'not-an-email',
        pais: 'Costa Rica',
      };

      const result = clienteSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should reject invalid genero', () => {
      const invalidData = {
        nombre: 'Juan Pérez',
        genero: 'Invalid',
        pais: 'Costa Rica',
      };

      const result = clienteSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should accept valid genero values', () => {
      const generos = ['M', 'F', 'X'];

      generos.forEach((genero) => {
        const data = {
          nombre: 'Test User',
          genero: genero,
          pais: 'Costa Rica',
        };
        const result = clienteSchema.safeParse(data);
        expect(result.success).toBe(true);
      });
    });

    test('should reject missing required fields', () => {
      const invalidData = {
        correo: 'juan@example.com',
      };

      const result = clienteSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });
  });

  describe('productoSchema', () => {
    test('should validate valid producto data', () => {
      const validData = {
        codigo_alt: 'PROD-001',
        nombre: 'Laptop Dell',
        categoria: 'Electrónica',
      };

      const result = productoSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should reject missing required fields', () => {
      const invalidData = {
        codigo_alt: 'PROD-001',
      };

      const result = productoSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should reject empty codigo_alt', () => {
      const invalidData = {
        codigo_alt: '',
        nombre: 'Product',
        categoria: 'Category',
      };

      const result = productoSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });
  });

  describe('ordenSchema', () => {
    test('should validate valid orden data with number', () => {
      const validData = {
        correo: 'customer@example.com',
        canal: 'WEB',
        total: 1500.50,
      };

      const result = ordenSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should validate valid orden data with string', () => {
      const validData = {
        correo: 'customer@example.com',
        canal: 'WEB',
        total: '1,500.50',
      };

      const result = ordenSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should accept any canal value (free text)', () => {
      const canales = ['WEB', 'TIENDA', 'APP', 'TELEFONO', 'EMAIL', 'Custom Channel'];

      canales.forEach((canal) => {
        const data = {
          correo: 'test@example.com',
          canal: canal,
          total: 100,
        };
        const result = ordenSchema.safeParse(data);
        expect(result.success).toBe(true);
      });
    });

    test('should reject empty canal', () => {
      const invalidData = {
        correo: 'test@example.com',
        canal: '',
        total: 100,
      };

      const result = ordenSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should reject invalid email', () => {
      const invalidData = {
        correo: 'not-an-email',
        canal: 'WEB',
        total: 100,
      };

      const result = ordenSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should accept valid moneda values', () => {
      const monedas = ['USD', 'CRC'];

      monedas.forEach((moneda) => {
        const data = {
          correo: 'test@example.com',
          canal: 'WEB',
          moneda: moneda,
          total: 100,
        };
        const result = ordenSchema.safeParse(data);
        expect(result.success).toBe(true);
      });
    });

    test('should reject invalid moneda', () => {
      const invalidData = {
        correo: 'test@example.com',
        canal: 'WEB',
        moneda: 'EUR',
        total: 100,
      };

      const result = ordenSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should default moneda to USD', () => {
      const data = {
        correo: 'test@example.com',
        canal: 'WEB',
        total: 100,
      };

      const result = ordenSchema.parse(data);
      expect(result.moneda).toBe('USD');
    });
  });

  describe('ordenDetalleSchema', () => {
    test('should validate valid orden detalle data with number', () => {
      const validData = {
        OrdenIndex: 1,
        codigo_alt: 'PROD-001',
        cantidad: 5,
        precio_unit: 100.50,
      };

      const result = ordenDetalleSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should validate valid orden detalle data with string', () => {
      const validData = {
        OrdenIndex: 1,
        codigo_alt: 'PROD-001',
        cantidad: 5,
        precio_unit: '100.50',
      };

      const result = ordenDetalleSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should reject negative cantidad', () => {
      const invalidData = {
        OrdenIndex: 1,
        codigo_alt: 'PROD-001',
        cantidad: -5,
        precio_unit: 100,
      };

      const result = ordenDetalleSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
    });

    test('should reject zero OrdenIndex', () => {
      const invalidData = {
        OrdenIndex: 0,
        codigo_alt: 'PROD-001',
        cantidad: 5,
        precio_unit: 100,
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
            nombre: 'Juan Pérez',
            correo: 'juan@example.com',
            pais: 'Costa Rica',
          },
        ],
        Producto: [
          {
            codigo_alt: 'PROD-001',
            nombre: 'Laptop',
            categoria: 'Electrónica',
          },
        ],
        Orden: [
          {
            correo: 'juan@example.com',
            canal: 'WEB',
            total: 1500,
          },
        ],
        OrdenDetalle: [
          {
            OrdenIndex: 1,
            codigo_alt: 'PROD-001',
            cantidad: 1,
            precio_unit: 1500,
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
            nombre: 'Juan Pérez',
            pais: 'Costa Rica',
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
