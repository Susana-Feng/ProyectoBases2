// Types for Excel data processing (MySQL schema - lowercase, Spanish)

export interface ClienteExcel {
  nombre: string;
  correo?: string; // Optional, NOT UNIQUE - duplicates allowed (heterogeneidad)
  genero: 'M' | 'F' | 'X'; // Required, ENUM with DEFAULT 'M' in DB
  pais: string;
  created_at?: Date | string; // Optional in Excel, will use current date if not provided
}

export interface ProductoExcel {
  codigo_alt: string; // Required, unique
  nombre: string;
  categoria: string;
}

export interface OrdenExcel {
  correo: string; // Required - Associates to Cliente by correo
                  // Strategy: 1) Looks in same Excel first (last match if duplicates)
                  //          2) If not found, searches DB (last inserted cliente)
                  // This allows partial Excel uploads (e.g., only Orden sheet)
  fecha?: Date | string; // Optional, will use current datetime if not provided
  canal: string; // Required - Free text (heterogeneidad)
  moneda: 'USD' | 'CRC'; // Required - CHAR(3) in MySQL
  total: number | string; // Required - VARCHAR in DB
}

export interface OrdenDetalleExcel {
  OrdenIndex: number; // Índice de la orden en el Excel (1-based)
  codigo_alt: string; // codigo_alt del producto (unique)
  cantidad: number;
  precio_unit: number | string; // VARCHAR - can be '100.50' or '100,50'
  // Note: No UNIQUE constraint on (orden_id, producto_id) - duplicates allowed
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

