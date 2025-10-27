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
          // total can be number or string
          total: row.total !== undefined ? row.total : undefined,
        }));
      } else if (sheetName === 'OrdenDetalle') {
        jsonData = jsonData.map((row: any) => ({
          ...row,
          OrdenIndex: row.OrdenIndex ? Number(row.OrdenIndex) : row.OrdenIndex,
          cantidad: row.cantidad ? Number(row.cantidad) : row.cantidad,
          // precio_unit can be number or string
          precio_unit: row.precio_unit !== undefined ? row.precio_unit : undefined,
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
 * Format date to MySQL VARCHAR format (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
 */
function formatDateForMySQL(date: Date | string, includeTime = false): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  
  if (!includeTime) {
    return `${year}-${month}-${day}`;
  }
  
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
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
      const correoToClienteId = new Map<string, number>();
      
      if (validatedData.Cliente && validatedData.Cliente.length > 0) {
        for (const cliente of validatedData.Cliente) {
          let result;
          
          // Only use upsert if correo exists (unique field)
          if (cliente.correo) {
            result = await tx.cliente.upsert({
              where: { correo: cliente.correo },
              update: {
                nombre: cliente.nombre,
                genero: cliente.genero, // Has default 'M' from Zod, NOT NULL in DB
                pais: cliente.pais,
              },
              create: {
                nombre: cliente.nombre,
                correo: cliente.correo,
                genero: cliente.genero, // Has default 'M' from Zod, NOT NULL in DB
                pais: cliente.pais,
                created_at: cliente.created_at 
                  ? formatDateForMySQL(cliente.created_at, false)
                  : formatDateForMySQL(new Date(), false),
              },
            });
            
            correoToClienteId.set(cliente.correo, result.id);
          } else {
            // If no correo, just create (can't upsert without unique field)
            result = await tx.cliente.create({
              data: {
                nombre: cliente.nombre,
                correo: null,
                genero: cliente.genero, // Has default 'M' from Zod, NOT NULL in DB
                pais: cliente.pais,
                created_at: cliente.created_at 
                  ? formatDateForMySQL(cliente.created_at, false)
                  : formatDateForMySQL(new Date(), false),
              },
            });
          }
          
          clientesInsertados++;
        }
      }

      // Step 2: Process Productos (if exists)
      const codigoAltToProductoId = new Map<string, number>();
      
      if (validatedData.Producto && validatedData.Producto.length > 0) {
        for (const producto of validatedData.Producto) {
          const result = await tx.producto.upsert({
            where: { codigo_alt: producto.codigo_alt },
            update: {
              nombre: producto.nombre,
              categoria: producto.categoria,
            },
            create: {
              codigo_alt: producto.codigo_alt,
              nombre: producto.nombre,
              categoria: producto.categoria,
            },
          });
          
          codigoAltToProductoId.set(producto.codigo_alt, result.id);
          productosInsertados++;
        }
      }

      // Step 3: Process Ordenes (if exists)
      const ordenIndexToOrdenId = new Map<number, number>();
      
      if (validatedData.Orden && validatedData.Orden.length > 0) {
        for (let i = 0; i < validatedData.Orden.length; i++) {
          const orden = validatedData.Orden[i];
          if (!orden) continue;
          
          // Get cliente_id by correo
          let clienteId = correoToClienteId.get(orden.correo);
          
          // If not in our map, search in database
          if (!clienteId) {
            const cliente = await tx.cliente.findUnique({
              where: { correo: orden.correo },
            });
            
            if (!cliente) {
              throw new Error(
                `Cliente with correo "${orden.correo}" not found for orden at index ${i + 1}. ` +
                `Please ensure the cliente exists in the Cliente sheet or database.`
              );
            }
            
            clienteId = cliente.id;
            correoToClienteId.set(orden.correo, clienteId);
          }

          const result = await tx.orden.create({
            data: {
              cliente_id: clienteId,
              fecha: orden.fecha 
                ? formatDateForMySQL(orden.fecha, true)
                : formatDateForMySQL(new Date(), true),
              canal: orden.canal,
              moneda: orden.moneda, // Has default 'USD' from Zod, NOT NULL in DB
              total: orden.total,
            },
          });
          
          // Map Excel row index (1-based) to orden id
          ordenIndexToOrdenId.set(i + 1, result.id);
          ordenesInsertadas++;
        }
      }

      // Step 4: Process OrdenDetalle (if exists)
      if (validatedData.OrdenDetalle && validatedData.OrdenDetalle.length > 0) {
        for (const detalle of validatedData.OrdenDetalle) {
          // Get orden id from our map
          const ordenId = ordenIndexToOrdenId.get(detalle.OrdenIndex);
          
          if (!ordenId) {
            throw new Error(
              `Orden at index ${detalle.OrdenIndex} not found. ` +
              `Please ensure the Orden sheet has a row at that position.`
            );
          }

          // Get producto id by codigo_alt
          let productoId = codigoAltToProductoId.get(detalle.codigo_alt);
          
          // If not in our map, search in database
          if (!productoId) {
            const producto = await tx.producto.findUnique({
              where: { codigo_alt: detalle.codigo_alt },
            });
            
            if (!producto) {
              throw new Error(
                `Producto with codigo_alt "${detalle.codigo_alt}" not found. ` +
                `Please ensure the producto exists in the Producto sheet or database.`
              );
            }
            
            productoId = producto.id;
            codigoAltToProductoId.set(detalle.codigo_alt, productoId);
          }

          await tx.ordenDetalle.create({
            data: {
              orden_id: ordenId,
              producto_id: productoId,
              cantidad: detalle.cantidad,
              precio_unit: detalle.precio_unit,
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
