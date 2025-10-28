// Pagination metadata
export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

// Cliente
export interface Cliente {
  id: number;
  nombre: string;
  correo: string | null;
  genero: string | null;
  pais: string;
  created_at: string;
}

// Producto
export interface Producto {
  id: number;
  codigo_alt: string;
  nombre: string;
  categoria: string;
}

// Orden
export interface Orden {
  id: number;
  cliente_id: number;
  fecha: string;
  canal: string;
  moneda: string;
  total: string;
}

// OrdenDetalle
export interface OrdenDetalle {
  id: number;
  orden_id: number;
  producto_id: number;
  cantidad: number;
  precio_unit: string;
}

// API Response types
export interface ListResponse<T> {
  success: boolean;
  data: T[];
  pagination: PaginationMeta;
}

export interface SingleResponse<T> {
  success: boolean;
  data: T;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  stats: {
    clientesInsertados: number;
    productosInsertados: number;
    ordenesInsertadas: number;
    detallesInsertados: number;
  };
}

export interface ErrorResponse {
  success: boolean;
  message: string;
  error?: string;
}

// Extended types with relations
export interface ClienteWithOrdenes extends Cliente {
  ordenes?: Orden[];
}

export interface ProductoWithDetalles extends Producto {
  ordenDetalles?: OrdenDetalle[];
}

export interface OrdenWithRelations extends Orden {
  cliente?: Cliente;
  detalles?: (OrdenDetalle & { producto?: Producto })[];
}

export interface OrdenDetalleWithRelations extends OrdenDetalle {
  orden?: Orden;
  producto?: Producto;
}
