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
        { Nombre: 'Test User', Email: 'test@example.com', Genero: 'Masculino', Pais: 'Test Country' },
      ];
      const wsCliente = XLSX.utils.json_to_sheet(clienteData);
      XLSX.utils.book_append_sheet(workbook, wsCliente, 'Cliente');
      
      const productoData = [
        { SKU: 'TEST-001', Nombre: 'Test Product', Categoria: 'Test Category' },
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
        { Nombre: 'Test User', Email: 'test@example.com', Genero: 'Masculino', Pais: 'Test Country' },
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
            Nombre: 'Juan Test',
            Email: 'juan.test@example.com',
            Genero: 'Masculino',
            Pais: 'Costa Rica',
            FechaRegistro: '2024-01-15',
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
        where: { Email: 'juan.test@example.com' },
      });
      expect(cliente).toBeDefined();
      expect(cliente?.Nombre).toBe('Juan Test');
    });

    test('should upsert existing Cliente by Email', async () => {
      // Insert first time
      const excelData1: ExcelData = {
        Cliente: [
          {
            Nombre: 'Original Name',
            Email: 'upsert.test@example.com',
            Genero: 'Masculino',
            Pais: 'Original Country',
          },
        ],
      };
      await processExcelData(excelData1);

      // Update with same Email
      const excelData2: ExcelData = {
        Cliente: [
          {
            Nombre: 'Updated Name',
            Email: 'upsert.test@example.com',
            Genero: 'Femenino',
            Pais: 'Updated Country',
          },
        ],
      };
      const result = await processExcelData(excelData2);

      expect(result.success).toBe(true);

      // Verify only one record exists with updated data
      const clientes = await prisma.cliente.findMany({
        where: { Email: 'upsert.test@example.com' },
      });
      expect(clientes).toHaveLength(1);
      expect(clientes[0]!.Nombre).toBe('Updated Name');
      expect(clientes[0]!.Pais).toBe('Updated Country');
    });

    test('should process Cliente without Email', async () => {
      const excelData: ExcelData = {
        Cliente: [
          {
            Nombre: 'No Email User',
            Pais: 'Test Country',
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
            SKU: 'TEST-PROD-001',
            Nombre: 'Test Product',
            Categoria: 'Test Category',
          },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(true);
      expect(result.stats?.productosInsertados).toBe(1);

      const producto = await prisma.producto.findUnique({
        where: { SKU: 'TEST-PROD-001' },
      });
      expect(producto).toBeDefined();
      expect(producto?.Nombre).toBe('Test Product');
    });

    test('should process complete workflow with all entities', async () => {
      const excelData: ExcelData = {
        Cliente: [
          {
            Nombre: 'Complete Test User',
            Email: 'complete@example.com',
            Genero: 'Masculino',
            Pais: 'Costa Rica',
          },
        ],
        Producto: [
          {
            SKU: 'COMPLETE-001',
            Nombre: 'Complete Product',
            Categoria: 'Electronics',
          },
        ],
        Orden: [
          {
            Email: 'complete@example.com',
            Fecha: '2024-01-20',
            Canal: 'WEB',
            Total: 1500.00,
          },
        ],
        OrdenDetalle: [
          {
            OrdenIndex: 1,
            SKU: 'COMPLETE-001',
            Cantidad: 1,
            PrecioUnit: 1500.00,
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
            Email: 'nonexistent@example.com',
            Fecha: '2024-01-20',
            Canal: 'WEB',
            Total: 1500.00,
          },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Cliente with email');
      expect(result.error).toContain('not found');
    });

    test('should fail when OrdenDetalle references non-existent Producto', async () => {
      // First create a cliente and orden
      const setupData: ExcelData = {
        Cliente: [
          {
            Nombre: 'Test User',
            Email: 'detalle.test@example.com',
            Pais: 'Test',
          },
        ],
        Orden: [
          {
            Email: 'detalle.test@example.com',
            Canal: 'WEB',
            Total: 100,
          },
        ],
      };
      await processExcelData(setupData);

      // Try to add detalle with non-existent SKU (must include Orden sheet for OrdenIndex mapping)
      const excelData: ExcelData = {
        Orden: [
          {
            Email: 'detalle.test@example.com',
            Canal: 'WEB',
            Total: 100,
          },
        ],
        OrdenDetalle: [
          {
            OrdenIndex: 1,
            SKU: 'NONEXISTENT-SKU',
            Cantidad: 1,
            PrecioUnit: 100,
          },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Producto with SKU');
      expect(result.error).toContain('not found');
    });

    test('should rollback transaction on error', async () => {
      const initialCount = await prisma.cliente.count();

      const excelData: ExcelData = {
        Cliente: [
          {
            Nombre: 'Should Rollback',
            Email: 'rollback@example.com',
            Pais: 'Test',
          },
        ],
        Orden: [
          {
            Email: 'nonexistent@example.com', // This will cause error
            Canal: 'WEB',
            Total: 100,
          },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(false);

      // Verify cliente was NOT inserted (transaction rollback)
      const finalCount = await prisma.cliente.count();
      expect(finalCount).toBe(initialCount);

      const cliente = await prisma.cliente.findUnique({
        where: { Email: 'rollback@example.com' },
      });
      expect(cliente).toBeNull();
    });

    test('should handle invalid data with Zod validation', async () => {
      const excelData: ExcelData = {
        Cliente: [
          {
            Nombre: 'Invalid Email User',
            Email: 'not-an-email', // Invalid email
            Pais: 'Test',
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
          { Nombre: 'User 1', Email: 'multi1@example.com', Pais: 'Country1' },
          { Nombre: 'User 2', Email: 'multi2@example.com', Pais: 'Country2' },
          { Nombre: 'User 3', Email: 'multi3@example.com', Pais: 'Country3' },
        ],
        Producto: [
          { SKU: 'MULTI-001', Nombre: 'Product 1', Categoria: 'Cat1' },
          { SKU: 'MULTI-002', Nombre: 'Product 2', Categoria: 'Cat2' },
        ],
      };

      const result = await processExcelData(excelData);

      expect(result.success).toBe(true);
      expect(result.stats?.clientesInsertados).toBe(3);
      expect(result.stats?.productosInsertados).toBe(2);
    });
  });
});

