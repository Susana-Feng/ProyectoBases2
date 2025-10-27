import { createRoute, z } from '@hono/zod-openapi';

// Schema for upload response success
const UploadSuccessSchema = z.object({
  success: z.boolean().openapi({ example: true }),
  message: z.string().openapi({ example: 'Excel data processed successfully' }),
  stats: z.object({
    clientesInsertados: z.number().openapi({ example: 2 }),
    productosInsertados: z.number().openapi({ example: 2 }),
    ordenesInsertadas: z.number().openapi({ example: 2 }),
    detallesInsertados: z.number().openapi({ example: 2 }),
  }).optional(),
}).openapi('UploadSuccess');

// Schema for error response
const ErrorResponseSchema = z.object({
  success: z.boolean().openapi({ example: false }),
  message: z.string().openapi({ example: 'Failed to process Excel data' }),
  error: z.string().optional().openapi({ 
    example: 'Cliente with correo "invalid@email.com" not found' 
  }),
}).openapi('ErrorResponse');

// Route for uploading Excel file
export const uploadExcelRoute = createRoute({
  method: 'post',
  path: '/excel',
  tags: ['Upload'],
  summary: 'Upload Excel file to MySQL',
  description: `Upload an Excel file (.xlsx or .xls) with data to insert into MySQL database.`,
  request: {
    body: {
      content: {
        'multipart/form-data': {
          schema: z.object({
            file: z.instanceof(File).openapi({
              type: 'string',
              format: 'binary',
              description: 'Excel file (.xlsx or .xls)',
            }),
          }),
        },
      },
      required: true,
    },
  },
  responses: {
    200: {
      content: {
        'application/json': {
          schema: UploadSuccessSchema,
        },
      },
      description: 'Excel file processed successfully',
    },
    400: {
      content: {
        'application/json': {
          schema: ErrorResponseSchema,
        },
      },
      description: 'Invalid file or missing required data',
    },
    422: {
      content: {
        'application/json': {
          schema: ErrorResponseSchema,
        },
      },
      description: 'Validation error or database constraint violation',
    },
    500: {
      content: {
        'application/json': {
          schema: ErrorResponseSchema,
        },
      },
      description: 'Internal server error',
    },
  },
});


