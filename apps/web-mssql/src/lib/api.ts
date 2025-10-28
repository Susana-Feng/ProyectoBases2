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

const API_BASE = "http://localhost:3000/api/v1";

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
  email?: string;
  pais?: string;
  genero?: string;
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
  sku?: string;
  categoria?: string;
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
  moneda?: string;
  fechaDesde?: string;
  fechaHasta?: string;
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
