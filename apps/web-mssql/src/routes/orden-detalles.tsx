import { useEffect, useState } from "react";
import { toast } from "sonner";

// Custom hook for debouncing values
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
import type { ColumnConfig } from "@/components/data-table";
import { DataTable } from "@/components/data-table";
import { RelatedDataCell } from "@/components/related-data-cell";
import { fetchOrdenDetalles, fetchOrdenData, fetchProductoData } from "@/lib/api";
import type { OrdenDetalle, PaginationMeta } from "@/types/api";

export default function OrdenDetallesPage() {
  const [data, setData] = useState<OrdenDetalle[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta>({
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [sortBy, setSortBy] = useState<string | undefined>();
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [filters, setFilters] = useState<Record<string, string>>({
    OrdenId: "",
    ProductoId: "",
  });

  // Debounce filters to avoid excessive API calls
  const debouncedFilters = useDebounce(filters, 300);

  const columns: ColumnConfig[] = [
    {
      key: "OrdenDetalleId",
      label: "Identificador",
      sortable: true,
      minWidth: 60,
      maxWidth: 80,
      priority: 1,
    },
    {
      key: "OrdenId",
      label: "Orden",
      sortable: true,
      minWidth: 80,
      maxWidth: 100,
      priority: 2,
      render: (value: number) => (
        <RelatedDataCell
          id={value}
          title="Detalles de la orden"
          fetchFn={fetchOrdenData}
          displayFields={[
            { key: "OrdenId", label: "Identificador" },
            { key: "ClienteId", label: "Cliente" },
            { key: "Fecha", label: "Fecha" },
            { key: "Canal", label: "Canal" },
            { key: "Moneda", label: "Moneda" },
            { key: "Total", label: "Total" },
          ]}
        />
      ),
    },
    {
      key: "ProductoId",
      label: "Producto",
      sortable: true,
      minWidth: 90,
      maxWidth: 120,
      priority: 3,
      render: (value: number) => (
        <RelatedDataCell
          id={value}
          title="Detalles del producto"
          fetchFn={fetchProductoData}
          displayFields={[
            { key: "ProductoId", label: "Identificador" },
            { key: "SKU", label: "Código SKU" },
            { key: "Nombre", label: "Nombre" },
            { key: "Categoria", label: "Categoría" },
          ]}
        />
      ),
    },
    {
      key: "Cantidad",
      label: "Cantidad",
      sortable: true,
      filterable: true,
      filterType: "number",
      minWidth: 70,
      maxWidth: 90,
      priority: 4,
    },
    {
      key: "PrecioUnit",
      label: "Precio unitario",
      sortable: true,
      filterable: true,
      filterType: "number",
      minWidth: 100,
      maxWidth: 130,
      priority: 5,
      format: (value) => {
        const num = parseFloat(value);
        return `$${num.toFixed(2)}`;
      },
    },
    {
      key: "DescuentoPct",
      label: "Descuento %",
      sortable: true,
      filterable: true,
      filterType: "number",
      minWidth: 90,
      maxWidth: 110,
      priority: 6,
      format: (value) => {
        if (!value) return "0%";
        const num = parseFloat(value);
        return `${num.toFixed(2)}%`;
      },
    },
  ];


  const loadData = async () => {
    setIsLoading(true);
    try {
      const response = await fetchOrdenDetalles({
        page: pagination.page,
        limit: pagination.limit,
        sortBy: sortBy,
        sortOrder: sortOrder,
        ordenId: debouncedFilters.OrdenId ? parseInt(debouncedFilters.OrdenId) : undefined,
        productoId: debouncedFilters.ProductoId ? parseInt(debouncedFilters.ProductoId) : undefined,
        cantidadMin: debouncedFilters.Cantidad_min ? parseInt(debouncedFilters.Cantidad_min) : undefined,
        cantidadMax: debouncedFilters.Cantidad_max ? parseInt(debouncedFilters.Cantidad_max) : undefined,
        precioUnitMin: debouncedFilters.PrecioUnit_min ? parseFloat(debouncedFilters.PrecioUnit_min) : undefined,
        precioUnitMax: debouncedFilters.PrecioUnit_max ? parseFloat(debouncedFilters.PrecioUnit_max) : undefined,
        descuentoMin: debouncedFilters.DescuentoPct_min ? parseFloat(debouncedFilters.DescuentoPct_min) : undefined,
        descuentoMax: debouncedFilters.DescuentoPct_max ? parseFloat(debouncedFilters.DescuentoPct_max) : undefined,
      });

      setData(response.data);
      setPagination(response.pagination);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Error desconocido";
      toast.error("Error al cargar detalles de órdenes", {
        description: errorMessage,
        position: "bottom-right",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [pagination.page, pagination.limit, sortBy, sortOrder, debouncedFilters]);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground">Detalles de órdenes</h1>
        <p className="text-muted-foreground mt-2">
          Gestiona y visualiza todos los detalles de órdenes en la base de datos
        </p>
      </div>

      <DataTable
        columns={columns}
        data={data}
        pagination={pagination}
        isLoading={isLoading}
        onPageChange={(page) =>
          setPagination((prev) => ({ ...prev, page }))
        }
        onLimitChange={(limit) =>
          setPagination((prev) => ({ ...prev, limit, page: 1 }))
        }
        onSort={(key, order) => {
          setSortBy(key || undefined);
          setSortOrder(order);
        }}
        sortBy={sortBy}
        sortOrder={sortOrder}
        filters={filters}
        onFilterChange={(key, value) => {
          setFilters((prev) => ({ ...prev, [key]: value }));
          setPagination((prev) => ({ ...prev, page: 1 }));
        }}
        getRowKey={(row) => `orden-detalle-${row.OrdenDetalleId}`}
      />
    </div>
  );
}
