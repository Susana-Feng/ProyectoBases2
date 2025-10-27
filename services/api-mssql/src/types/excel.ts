// Types for Excel data processing

export interface ClienteExcel {
  Nombre: string;
  Email?: string;
  Genero?: 'Masculino' | 'Femenino';
  Pais: string;
  FechaRegistro?: Date | string;
}

export interface ProductoExcel {
  SKU: string;
  Nombre: string;
  Categoria: string;
}

export interface OrdenExcel {
  Email: string; // Email del cliente (identificador natural)
  Fecha?: Date | string;
  Canal: 'WEB' | 'TIENDA' | 'APP';
  Moneda?: string;
  Total: number;
}

export interface OrdenDetalleExcel {
  OrdenIndex: number; // Índice de la orden en el Excel (1-based)
  SKU: string; // SKU del producto (identificador natural)
  Cantidad: number;
  PrecioUnit: number;
  DescuentoPct?: number;
}

export interface ExcelData {
  Cliente?: ClienteExcel[];
  Producto?: ProductoExcel[];
  Orden?: OrdenExcel[];
  OrdenDetalle?: OrdenDetalleExcel[];
}

export interface ProcessResult {
  success: boolean;
  message: string;
  stats?: {
    clientesInsertados: number;
    productosInsertados: number;
    ordenesInsertadas: number;
    detallesInsertados: number;
  };
  error?: string;
}

