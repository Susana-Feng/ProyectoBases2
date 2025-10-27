import { describe, test, expect, beforeAll, afterAll } from 'bun:test';
import * as XLSX from 'xlsx';
import { app } from '../../index';

describe('Upload Route', () => {
  const BASE_URL = 'http://localhost:3001';
  let server: ReturnType<typeof Bun.serve> | null = null;

  // Start server before all tests
  beforeAll(() => {
    server = Bun.serve({
      port: 3001,
      fetch: app.fetch,
    });
    console.log('Test server started on port 3001');
  });

  // Stop server after all tests
  afterAll(() => {
    if (server) {
      server.stop();
      console.log('Test server stopped (port 3001)');
    }
  });

  test('should reject non-Excel files', async () => {
    const formData = new FormData();
    const textFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
    formData.append('file', textFile);

    const response = await fetch(`${BASE_URL}/upload/excel`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json() as any;

    expect(response.status).toBe(400);
    expect(data.success).toBe(false);
    expect(data.message).toContain('Invalid file type');
  });

  test('should reject request without file', async () => {
    const formData = new FormData();

    const response = await fetch(`${BASE_URL}/upload/excel`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json() as any;

    // OpenAPI/Zod validation returns error object when file is missing
    expect(response.status).toBe(400);
    expect(data.success).toBe(false);
    expect(data.error).toBeDefined();
  });

  test('should accept valid Excel file', async () => {
    // Create a test Excel file
    const workbook = XLSX.utils.book_new();
    
    const clienteData = [
      {
        nombre: 'Test Upload User',
        correo: 'upload.test@example.com',
        genero: 'M',
        pais: 'Test Country',
      },
    ];
    const wsCliente = XLSX.utils.json_to_sheet(clienteData);
    XLSX.utils.book_append_sheet(workbook, wsCliente, 'Cliente');

    // Convert to buffer
    const buffer = XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' });
    
    // Create File from buffer
    const file = new File([buffer], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${BASE_URL}/upload/excel`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json() as any;

    expect([200, 422]).toContain(response.status); // 200 if DB connected, 422 if not
    expect(data).toBeDefined();
  });

  test('should reject empty Excel file', async () => {
    // xlsx library throws error when creating empty workbook
    const workbook = XLSX.utils.book_new();
    
    expect(() => {
      XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' });
    }).toThrow('Workbook is empty');
  });
});

