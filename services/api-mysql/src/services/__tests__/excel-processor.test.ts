import { describe, test, expect, beforeAll, afterAll } from 'bun:test';
import { parseExcelFile, processExcelData } from '../excel-processor';
import * as XLSX from 'xlsx';
import type { ExcelData } from '../../types/excel';
import { prisma } from '../../lib/prisma';

describe('Excel Processor', () => {
  // Cleanup after all tests
  afterAll(async () => {
    // Clean up test data
    try {
      await prisma.ordenDetalle.deleteMany({});
      await prisma.orden.deleteMany({});
      await prisma.producto.deleteMany({});
      await prisma.cliente.deleteMany({});
    } catch (error) {
      console.error('Cleanup error:', error);
    } finally {
      await prisma.$disconnect();
    }
  });

  describe('parseExcelFile', () => {
    test('should parse Excel file with all sheets', () => {
      // Create a test workbook
      const workbook = XLSX.utils.book_new();
      
      const clienteData = [
        { nombre: 'Test User', correo: 'test@example.com', genero: 'M', pais: 'Test Country' },
      ];
      const wsCliente = XLSX.utils.json_to_sheet(clienteData);
      XLSX.utils.book_append_sheet(workbook, wsCliente, 'Cliente');
      
      const productoData = [
        { codigo_alt: 'TEST-001', nombre: 'Test Product', categoria: 'Test Category' },
      ];
      const wsProducto = XLSX.utils.json_to_sheet(productoData);
      XLSX.utils.book_append_sheet(workbook, wsProducto, 'Producto');
      
      // Convert to buffer
      const buffer = XLSX.write(workbook, { type: 'array', bookType: 'xlsx' });
      
      // Parse
      const result = parseExcelFile(buffer);
      
      expect(result).toBeDefined();
      expect(result.Cliente).toBeDefined();
      expect(result.Cliente).toHaveLength(1);
      expect(result.Producto).toBeDefined();
      expect(result.Producto).toHaveLength(1);
    });

  test('should handle empty Excel file', () => {
    const workbook = XLSX.utils.book_new();
    
    // xlsx library throws error when trying to write empty workbook
    expect(() => {
      XLSX.write(workbook, { type: 'array', bookType: 'xlsx' });
    }).toThrow('Workbook is empty');
  });

    test('should parse only existing sheets', () => {
      const workbook = XLSX.utils.book_new();
      
      const clienteData = [
        { nombre: 'Test User', correo: 'test@example.com', genero: 'M', pais: 'Test Country' },
      ];
      const wsCliente = XLSX.utils.json_to_sheet(clienteData);
      XLSX.utils.book_append_sheet(workbook, wsCliente, 'Cliente');
      
      const buffer = XLSX.write(workbook, { type: 'array', bookType: 'xlsx' });
      const result = parseExcelFile(buffer);
      
      expect(result.Cliente).toBeDefined();
      expect(result.Producto).toBeUndefined();
      expect(result.Orden).toBeUndefined();
      expect(result.OrdenDetalle).toBeUndefined();
    });
  });

  describe('processExcelData', () => {
    test('should process valid Cliente data', async () => {
      const excelData: ExcelData = {
        Cliente: [
          {
            nombre: 'Juan Test',
            correo: 'juan.test@example.com',
            genero: 'M',
            pais: 'Costa Rica',
            created_at: '2024-01-15',
          },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(true);
      expect(result.stats?.clientesInsertados).toBe(1);
      expect(result.stats?.productosInsertados).toBe(0);
      expect(result.stats?.ordenesInsertadas).toBe(0);
      expect(result.stats?.detallesInsertados).toBe(0);

      // Verify data was inserted
      const cliente = await prisma.cliente.findUnique({
        where: { correo: 'juan.test@example.com' },
      });
      expect(cliente).toBeDefined();
      expect(cliente?.nombre).toBe('Juan Test');
    });

    test('should upsert existing Cliente by correo', async () => {
      // Insert first time
      const excelData1: ExcelData = {
        Cliente: [
          {
            nombre: 'Original Name',
            correo: 'upsert.test@example.com',
            genero: 'M',
            pais: 'Original Country',
          },
        ],
      };
      await processExcelData(excelData1);

      // Update with same correo
      const excelData2: ExcelData = {
        Cliente: [
          {
            nombre: 'Updated Name',
            correo: 'upsert.test@example.com',
            genero: 'F',
            pais: 'Updated Country',
          },
        ],
      };
      const result = await processExcelData(excelData2);

      expect(result.success).toBe(true);

      // Verify only one record exists with updated data
      const clientes = await prisma.cliente.findMany({
        where: { correo: 'upsert.test@example.com' },
      });
      expect(clientes).toHaveLength(1);
      expect(clientes[0]!.nombre).toBe('Updated Name');
      expect(clientes[0]!.pais).toBe('Updated Country');
    });

    test('should process Cliente without correo', async () => {
      const excelData: ExcelData = {
        Cliente: [
          {
            nombre: 'No Email User',
            genero: 'X',
            pais: 'Test Country',
          },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(true);
      expect(result.stats?.clientesInsertados).toBe(1);
    });

    test('should process valid Producto data', async () => {
      const excelData: ExcelData = {
        Producto: [
          {
            codigo_alt: 'TEST-PROD-001',
            nombre: 'Test Product',
            categoria: 'Test Category',
          },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(true);
      expect(result.stats?.productosInsertados).toBe(1);

      const producto = await prisma.producto.findUnique({
        where: { codigo_alt: 'TEST-PROD-001' },
      });
      expect(producto).toBeDefined();
      expect(producto?.nombre).toBe('Test Product');
    });

    test('should process complete workflow with all entities', async () => {
      const excelData: ExcelData = {
        Cliente: [
          {
            nombre: 'Complete Test User',
            correo: 'complete@example.com',
            genero: 'M',
            pais: 'Costa Rica',
          },
        ],
        Producto: [
          {
            codigo_alt: 'COMPLETE-001',
            nombre: 'Complete Product',
            categoria: 'Electronics',
          },
        ],
        Orden: [
          {
            correo: 'complete@example.com',
            fecha: '2024-01-20',
            canal: 'WEB',
            moneda: 'USD',
            total: 1500.00,
          },
        ],
        OrdenDetalle: [
          {
            OrdenIndex: 1,
            codigo_alt: 'COMPLETE-001',
            cantidad: 1,
            precio_unit: 1500.00,
          },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(true);
      expect(result.stats?.clientesInsertados).toBe(1);
      expect(result.stats?.productosInsertados).toBe(1);
      expect(result.stats?.ordenesInsertadas).toBe(1);
      expect(result.stats?.detallesInsertados).toBe(1);
    });

    test('should fail when Orden references non-existent Cliente', async () => {
      const excelData: ExcelData = {
        Orden: [
          {
            correo: 'nonexistent@example.com',
            fecha: '2024-01-20',
            canal: 'WEB',
            moneda: 'USD',
            total: 1500.00,
          },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Cliente with correo');
      expect(result.error).toContain('not found');
    });

    test('should fail when OrdenDetalle references non-existent Producto', async () => {
      // First create a cliente and orden
      const setupData: ExcelData = {
        Cliente: [
          {
            nombre: 'Test User',
            correo: 'detalle.test@example.com',
            genero: 'M',
            pais: 'Test',
          },
        ],
        Orden: [
          {
            correo: 'detalle.test@example.com',
            canal: 'WEB',
            moneda: 'USD',
            total: 100,
          },
        ],
      };
      await processExcelData(setupData);

      // Try to add detalle with non-existent codigo_alt (must include Orden sheet for OrdenIndex mapping)
      const excelData: ExcelData = {
        Orden: [
          {
            correo: 'detalle.test@example.com',
            canal: 'WEB',
            moneda: 'USD',
            total: 100,
          },
        ],
        OrdenDetalle: [
          {
            OrdenIndex: 1,
            codigo_alt: 'NONEXISTENT-SKU',
            cantidad: 1,
            precio_unit: 100,
          },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Producto with codigo_alt');
      expect(result.error).toContain('not found');
    });

    test('should rollback transaction on error', async () => {
      const initialCount = await prisma.cliente.count();

      const excelData: ExcelData = {
        Cliente: [
          {
            nombre: 'Should Rollback',
            correo: 'rollback@example.com',
            genero: 'M',
            pais: 'Test',
          },
        ],
        Orden: [
          {
            correo: 'nonexistent@example.com', // This will cause error
            canal: 'WEB',
            moneda: 'USD',
            total: 100,
          },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(false);

      // Verify cliente was NOT inserted (transaction rollback)
      const finalCount = await prisma.cliente.count();
      expect(finalCount).toBe(initialCount);

      const cliente = await prisma.cliente.findUnique({
        where: { correo: 'rollback@example.com' },
      });
      expect(cliente).toBeNull();
    });

    test('should handle invalid data with Zod validation', async () => {
      const excelData: ExcelData = {
        Cliente: [
          {
            nombre: 'Invalid Email User',
            correo: 'not-an-email', // Invalid email
            genero: 'M',
            pais: 'Test',
          } as any,
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    test('should process multiple items in transaction', async () => {
      const excelData: ExcelData = {
        Cliente: [
          { nombre: 'User 1', correo: 'multi1@example.com', genero: 'M', pais: 'Country1' },
          { nombre: 'User 2', correo: 'multi2@example.com', genero: 'F', pais: 'Country2' },
          { nombre: 'User 3', correo: 'multi3@example.com', genero: 'X', pais: 'Country3' },
        ],
        Producto: [
          { codigo_alt: 'MULTI-001', nombre: 'Product 1', categoria: 'Cat1' },
          { codigo_alt: 'MULTI-002', nombre: 'Product 2', categoria: 'Cat2' },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(true);
      expect(result.stats?.clientesInsertados).toBe(3);
      expect(result.stats?.productosInsertados).toBe(2);
    });
  });
});
