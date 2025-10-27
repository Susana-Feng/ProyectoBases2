import { OpenAPIHono } from '@hono/zod-openapi';
import { parseExcelFile, processExcelData } from '../services/excel-processor';
import { uploadExcelRoute } from './upload.openapi';

const upload = new OpenAPIHono();

// POST /upload/excel - Upload and process Excel file
upload.openapi(uploadExcelRoute, async (c) => {
  try {
    // Parse form data
    const body = await c.req.parseBody();
    const file = body['file'];

    // Validate file exists
    if (!file || !(file instanceof File)) {
      return c.json(
        {
          success: false,
          message: 'No file uploaded or invalid file format',
        },
        400
      );
    }

    // Validate file is Excel
    const allowedTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
      'application/vnd.ms-excel', // .xls
    ];

    if (!allowedTypes.includes(file.type) && 
        !file.name.endsWith('.xlsx') && 
        !file.name.endsWith('.xls')) {
      return c.json(
        {
          success: false,
          message: 'Invalid file type. Only Excel files (.xlsx, .xls) are allowed',
        },
        400
      );
    }

    // Read file as ArrayBuffer
    const arrayBuffer = await file.arrayBuffer();

    // Parse Excel file
    console.log('Parsing Excel file...');
    const excelData = parseExcelFile(arrayBuffer);

    // Validate that at least one sheet exists
    if (!excelData.Cliente && !excelData.Producto && !excelData.Orden && !excelData.OrdenDetalle) {
      return c.json(
        {
          success: false,
          message: 'Excel file must contain at least one valid sheet (Cliente, Producto, Orden, or OrdenDetalle)',
        },
        400
      );
    }

    // Process data and insert to database
    console.log('Processing Excel data...');
    const result = await processExcelData(excelData);

    if (!result.success) {
      return c.json(result, 422);
    }

    return c.json(result, 200);
  } catch (error) {
    console.error('Error in upload endpoint:', error);
    
    return c.json(
      {
        success: false,
        message: 'Internal server error',
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      500
    );
  }
});

export default upload;

