// Types for Excel data processing (MySQL schema - lowercase, Spanish)

export interface ClienteExcel {
  nombre: string;
  correo?: string; // Optional in Excel, unique in DB
  genero: 'M' | 'F' | 'X'; // Required, DEFAULT 'M' in DB
  pais: string;
  created_at?: Date | string; // Optional in Excel, will use current date if not provided
}

export interface ProductoExcel {
  codigo_alt: string; // Required, unique
  nombre: string;
  categoria: string;
}

export interface OrdenExcel {
  correo: string; // Required - correo del cliente (identificador natural)
  fecha?: Date | string; // Optional, will use current datetime if not provided
  canal: string; // Required - Free text (heterogeneidad)
  moneda: 'USD' | 'CRC'; // Required - ENUM in MySQL
  total: number | string; // Required - VARCHAR in DB
}

export interface OrdenDetalleExcel {
  OrdenIndex: number; // Índice de la orden en el Excel (1-based)
  codigo_alt: string; // codigo_alt del producto (identificador natural)
  cantidad: number;
  precio_unit: number | string;
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

