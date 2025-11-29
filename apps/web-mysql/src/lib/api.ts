import type {
  Cliente,
  ListResponse,
  Orden,
  OrdenDetalle,
  Producto,
  UploadResponse,
  ErrorResponse,
  SingleResponse,
  ClienteWithOrdenes,
  OrdenWithRelations,
  OrdenDetalleWithRelations,
  ProductoWithDetalles,
} from "@/types/api";

const DEFAULT_API_BASE = "http://localhost:3001/api/v1";

const apiBaseFromEnv =
  typeof globalThis !== "undefined" && (globalThis as any)?.Bun?.env?.VITE_API_URL
    ? (globalThis as any).Bun.env.VITE_API_URL
    : undefined;

const API_BASE = apiBaseFromEnv ?? import.meta.env.VITE_API_URL ?? DEFAULT_API_BASE;

// Helper function to build query parameters
function buildQueryParams(params: Record<string, any>): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.append(key, String(value));
    }
  });
  return searchParams.toString();
}

// Helper function for error handling
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.message || `API Error: ${response.statusText}`);
  }
  return response.json();
}

// Clientes
export async function fetchClientes(params: {
  page?: number;
  limit?: number;
  nombre?: string;
  nombreExact?: boolean;
  correo?: string;
  correoExact?: boolean;
  pais?: string;
  paisExact?: boolean;
  genero?: string;
  createdAtDesde?: string;
  createdAtHasta?: string;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}): Promise<ListResponse<Cliente>> {
  const query = buildQueryParams(params);
  const url = `${API_BASE}/clientes${query ? "?" + query : ""}`;
  const response = await fetch(url);
  return handleResponse<ListResponse<Cliente>>(response);
}

export async function fetchClienteById(
  id: number,
  include?: string
): Promise<SingleResponse<ClienteWithOrdenes>> {
  const query = buildQueryParams({ include });
  const url = `${API_BASE}/clientes/${id}${query ? "?" + query : ""}`;
  const response = await fetch(url);
  return handleResponse<SingleResponse<ClienteWithOrdenes>>(response);
}

// Productos
export async function fetchProductos(params: {
  page?: number;
  limit?: number;
  nombre?: string;
  nombreExact?: boolean;
  codigoAlt?: string;
  codigoAltExact?: boolean;
  categoria?: string;
  categoriaExact?: boolean;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}): Promise<ListResponse<Producto>> {
  const query = buildQueryParams(params);
  const url = `${API_BASE}/productos${query ? "?" + query : ""}`;
  const response = await fetch(url);
  return handleResponse<ListResponse<Producto>>(response);
}

export async function fetchProductoById(
  id: number,
  include?: string
): Promise<SingleResponse<ProductoWithDetalles>> {
  const query = buildQueryParams({ include });
  const url = `${API_BASE}/productos/${id}${query ? "?" + query : ""}`;
  const response = await fetch(url);
  return handleResponse<SingleResponse<ProductoWithDetalles>>(response);
}

// Órdenes
export async function fetchOrdenes(params: {
  page?: number;
  limit?: number;
  clienteId?: number;
  canal?: string;
  canalExact?: boolean;
  moneda?: string;
  fechaDesde?: string;
  fechaHasta?: string;
  totalMin?: number;
  totalMax?: number;
  totalGt?: number;
  totalLt?: number;
  totalEq?: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}): Promise<ListResponse<Orden>> {
  const query = buildQueryParams(params);
  const url = `${API_BASE}/ordenes${query ? "?" + query : ""}`;
  const response = await fetch(url);
  return handleResponse<ListResponse<Orden>>(response);
}

export async function fetchOrdenById(
  id: number,
  include?: string
): Promise<SingleResponse<OrdenWithRelations>> {
  const query = buildQueryParams({ include });
  const url = `${API_BASE}/ordenes/${id}${query ? "?" + query : ""}`;
  const response = await fetch(url);
  return handleResponse<SingleResponse<OrdenWithRelations>>(response);
}

// Orden Detalles
export async function fetchOrdenDetalles(params: {
  page?: number;
  limit?: number;
  ordenId?: number;
  productoId?: number;
  cantidadMin?: number;
  cantidadMax?: number;
  cantidadGt?: number;
  cantidadLt?: number;
  cantidadEq?: number;
  precioUnitMin?: number;
  precioUnitMax?: number;
  precioUnitGt?: number;
  precioUnitLt?: number;
  precioUnitEq?: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}): Promise<ListResponse<OrdenDetalle>> {
  const query = buildQueryParams(params);
  const url = `${API_BASE}/orden-detalles${query ? "?" + query : ""}`;
  const response = await fetch(url);
  return handleResponse<ListResponse<OrdenDetalle>>(response);
}

export async function fetchOrdenDetalleById(
  id: number,
  include?: string
): Promise<SingleResponse<OrdenDetalleWithRelations>> {
  const query = buildQueryParams({ include });
  const url = `${API_BASE}/orden-detalles/${id}${query ? "?" + query : ""}`;
  const response = await fetch(url);
  return handleResponse<SingleResponse<OrdenDetalleWithRelations>>(response);
}

// Upload
export async function uploadExcelFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/upload/excel`, {
    method: "POST",
    body: formData,
  });

  return handleResponse<UploadResponse>(response);
}

// Helper functions for fetching related data with caching
const relationshipCache = new Map<string, { data: any; timestamp: number }>();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

function getCacheKey(type: string, id: number): string {
  return `${type}:${id}`;
}

function getFromCache(key: string): any | null {
  const cached = relationshipCache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.data;
  }
  relationshipCache.delete(key);
  return null;
}

function setInCache(key: string, data: any): void {
  relationshipCache.set(key, { data, timestamp: Date.now() });
}

// Fetch Cliente with caching
export async function fetchClienteData(
  id: number
): Promise<SingleResponse<Cliente>> {
  const cacheKey = getCacheKey("cliente", id);
  const cached = getFromCache(cacheKey);
  if (cached) {
    return { success: true, data: cached };
  }

  const response = await fetchClienteById(id);
  setInCache(cacheKey, response.data);
  return response;
}

// Fetch Producto with caching
export async function fetchProductoData(
  id: number
): Promise<SingleResponse<Producto>> {
  const cacheKey = getCacheKey("producto", id);
  const cached = getFromCache(cacheKey);
  if (cached) {
    return { success: true, data: cached };
  }

  const response = await fetchProductoById(id);
  setInCache(cacheKey, response.data);
  return response;
}

// Fetch Orden with caching
export async function fetchOrdenData(
  id: number
): Promise<SingleResponse<Orden>> {
  const cacheKey = getCacheKey("orden", id);
  const cached = getFromCache(cacheKey);
  if (cached) {
    return { success: true, data: cached };
  }

  const response = await fetchOrdenById(id);
  setInCache(cacheKey, response.data);
  return response;
}
