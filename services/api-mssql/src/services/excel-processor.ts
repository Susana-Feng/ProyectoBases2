import * as XLSX from 'xlsx';
import { prisma } from '../lib/prisma';
import type { ExcelData, ProcessResult } from '../types/excel';
import { excelDataSchema } from '../validators/excel-schemas';

/**
 * Parse Excel file to ExcelData structure
 */
export function parseExcelFile(buffer: ArrayBuffer): ExcelData {
  const workbook = XLSX.read(buffer, { type: 'array' });
  const data: ExcelData = {};

  // Parse each sheet if it exists
  const sheetNames = ['Cliente', 'Producto', 'Orden', 'OrdenDetalle'];

  for (const sheetName of sheetNames) {
    if (workbook.SheetNames.includes(sheetName)) {
      const worksheet = workbook.Sheets[sheetName];
      if (!worksheet) continue;
      
      let jsonData = XLSX.utils.sheet_to_json(worksheet);
      
      // Type conversion based on sheet name
      if (sheetName === 'Orden') {
        jsonData = jsonData.map((row: any) => ({
          ...row,
          Total: row.Total ? Number(row.Total) : row.Total,
        }));
      } else if (sheetName === 'OrdenDetalle') {
        jsonData = jsonData.map((row: any) => ({
          ...row,
          OrdenIndex: row.OrdenIndex ? Number(row.OrdenIndex) : row.OrdenIndex,
          Cantidad: row.Cantidad ? Number(row.Cantidad) : row.Cantidad,
          PrecioUnit: row.PrecioUnit ? Number(row.PrecioUnit) : row.PrecioUnit,
          DescuentoPct: row.DescuentoPct && row.DescuentoPct !== '' ? Number(row.DescuentoPct) : null,
        }));
      }
      
      if (jsonData.length > 0) {
        data[sheetName as keyof ExcelData] = jsonData as any;
      }
    }
  }

  return data;
}

/**
 * Process Excel data and insert into database with transaction
 */
export async function processExcelData(excelData: ExcelData): Promise<ProcessResult> {
  try {
    // Validate data with Zod
    const validatedData = excelDataSchema.parse(excelData);

    let clientesInsertados = 0;
    let productosInsertados = 0;
    let ordenesInsertadas = 0;
    let detallesInsertados = 0;

    // Use Prisma transaction to ensure all-or-nothing
    // Increase timeout for large Excel files (default is 5000ms)
    await prisma.$transaction(async (tx) => {
      // Step 1: Process Clientes (if exists)
      const emailToClienteId = new Map<string, number>();
      
      if (validatedData.Cliente && validatedData.Cliente.length > 0) {
        for (const cliente of validatedData.Cliente) {
          let result;
          
          // Only use upsert if Email exists (unique field)
          if (cliente.Email) {
            result = await tx.cliente.upsert({
              where: { Email: cliente.Email },
              update: {
                Nombre: cliente.Nombre,
                Genero: cliente.Genero || null,
                Pais: cliente.Pais,
              },
              create: {
                Nombre: cliente.Nombre,
                Email: cliente.Email,
                Genero: cliente.Genero || null,
                Pais: cliente.Pais,
                FechaRegistro: cliente.FechaRegistro 
                  ? new Date(cliente.FechaRegistro)
                  : new Date(),
              },
            });
            
            emailToClienteId.set(cliente.Email, result.ClienteId);
          } else {
            // If no Email, just create (can't upsert without unique field)
            result = await tx.cliente.create({
              data: {
                Nombre: cliente.Nombre,
                Email: null,
                Genero: cliente.Genero || null,
                Pais: cliente.Pais,
                FechaRegistro: cliente.FechaRegistro 
                  ? new Date(cliente.FechaRegistro)
                  : new Date(),
              },
            });
          }
          
          clientesInsertados++;
        }
      }

      // Step 2: Process Productos (if exists)
      const skuToProductoId = new Map<string, number>();
      
      if (validatedData.Producto && validatedData.Producto.length > 0) {
        for (const producto of validatedData.Producto) {
          const result = await tx.producto.upsert({
            where: { SKU: producto.SKU },
            update: {
              Nombre: producto.Nombre,
              Categoria: producto.Categoria,
            },
            create: {
              SKU: producto.SKU,
              Nombre: producto.Nombre,
              Categoria: producto.Categoria,
            },
          });
          
          skuToProductoId.set(producto.SKU, result.ProductoId);
          productosInsertados++;
        }
      }

      // Step 3: Process Ordenes (if exists)
      const ordenIndexToOrdenId = new Map<number, number>();
      
      if (validatedData.Orden && validatedData.Orden.length > 0) {
        for (let i = 0; i < validatedData.Orden.length; i++) {
          const orden = validatedData.Orden[i];
          if (!orden) continue;
          
          // Get ClienteId by Email
          let clienteId = emailToClienteId.get(orden.Email);
          
          // If not in our map, search in database
          if (!clienteId) {
            const cliente = await tx.cliente.findUnique({
              where: { Email: orden.Email },
            });
            
            if (!cliente) {
              throw new Error(
                `Cliente with email "${orden.Email}" not found for orden at index ${i + 1}. ` +
                `Please ensure the cliente exists in the Cliente sheet or database.`
              );
            }
            
            clienteId = cliente.ClienteId;
            emailToClienteId.set(orden.Email, clienteId);
          }

          const result = await tx.orden.create({
            data: {
              ClienteId: clienteId,
              Fecha: orden.Fecha ? new Date(orden.Fecha) : new Date(),
              Canal: orden.Canal,
              Moneda: orden.Moneda || 'USD',
              Total: orden.Total,
            },
          });
          
          // Map Excel row index (1-based) to OrdenId
          ordenIndexToOrdenId.set(i + 1, result.OrdenId);
          ordenesInsertadas++;
        }
      }

      // Step 4: Process OrdenDetalle (if exists)
      if (validatedData.OrdenDetalle && validatedData.OrdenDetalle.length > 0) {
        for (const detalle of validatedData.OrdenDetalle) {
          // Get OrdenId from our map
          const ordenId = ordenIndexToOrdenId.get(detalle.OrdenIndex);
          
          if (!ordenId) {
            throw new Error(
              `Orden at index ${detalle.OrdenIndex} not found. ` +
              `Please ensure the Orden sheet has a row at that position.`
            );
          }

          // Get ProductoId by SKU
          let productoId = skuToProductoId.get(detalle.SKU);
          
          // If not in our map, search in database
          if (!productoId) {
            const producto = await tx.producto.findUnique({
              where: { SKU: detalle.SKU },
            });
            
            if (!producto) {
              throw new Error(
                `Producto with SKU "${detalle.SKU}" not found. ` +
                `Please ensure the producto exists in the Producto sheet or database.`
              );
            }
            
            productoId = producto.ProductoId;
            skuToProductoId.set(detalle.SKU, productoId);
          }

          await tx.ordenDetalle.create({
            data: {
              OrdenId: ordenId,
              ProductoId: productoId,
              Cantidad: detalle.Cantidad,
              PrecioUnit: detalle.PrecioUnit,
              DescuentoPct: detalle.DescuentoPct ?? null,
            },
          });
          
          detallesInsertados++;
        }
      }
    }, {
      maxWait: 20000, // Wait up to 20 seconds for transaction to start
      timeout: 60000, // Allow transaction to run for up to 60 seconds
    });

    return {
      success: true,
      message: 'Excel data processed successfully',
      stats: {
        clientesInsertados,
        productosInsertados,
        ordenesInsertadas,
        detallesInsertados,
      },
    };
  } catch (error) {
    console.error('Error processing Excel data:', error);
    
    if (error instanceof Error) {
      return {
        success: false,
        message: 'Failed to process Excel data',
        error: error.message,
      };
    }
    
    return {
      success: false,
      message: 'Failed to process Excel data',
      error: 'Unknown error occurred',
    };
  }
}

