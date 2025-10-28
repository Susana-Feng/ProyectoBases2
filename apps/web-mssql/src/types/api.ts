// Pagination metadata
export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

// Cliente
export interface Cliente {
  ClienteId: number;
  Nombre: string;
  Email: string | null;
  Genero: string | null;
  Pais: string;
  FechaRegistro: string;
}

// Producto
export interface Producto {
  ProductoId: number;
  SKU: string;
  Nombre: string;
  Categoria: string;
}

// Orden
export interface Orden {
  OrdenId: number;
  ClienteId: number;
  Fecha: string;
  Canal: string;
  Moneda: string;
  Total: string;
}

// OrdenDetalle
export interface OrdenDetalle {
  OrdenDetalleId: number;
  OrdenId: number;
  ProductoId: number;
  Cantidad: number;
  PrecioUnit: string;
  DescuentoPct: string | null;
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
