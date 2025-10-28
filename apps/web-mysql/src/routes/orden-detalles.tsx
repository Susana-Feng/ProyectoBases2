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

// Helper function to get currency symbol
function getCurrencySymbol(currency: string): string {
  switch (currency) {
    case "USD":
      return "$";
    case "CRC":
      return "₡";
    default:
      return "$";
  }
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
    orden_id: "",
    producto_id: "",
  });
  const [monedaMap, setMonedaMap] = useState<Record<number, string>>({}); // Map of orden_id -> moneda

  // Debounce filters to avoid excessive API calls
  const debouncedFilters = useDebounce(filters, 300);

  const columns: ColumnConfig[] = [
    {
      key: "id",
      label: "Identificador",
      sortable: true,
      minWidth: 60,
      maxWidth: 80,
      priority: 1,
    },
    {
      key: "orden_id",
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
            { key: "id", label: "Identificador" },
            { key: "cliente_id", label: "Cliente" },
            { key: "fecha", label: "Fecha" },
            { key: "canal", label: "Canal" },
            { key: "moneda", label: "Moneda" },
            { key: "total", label: "Total" },
          ]}
        />
      ),
    },
    {
      key: "producto_id",
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
            { key: "id", label: "Identificador" },
            { key: "codigo_alt", label: "Código" },
            { key: "nombre", label: "Nombre" },
            { key: "categoria", label: "Categoría" },
          ]}
        />
      ),
    },
    {
      key: "cantidad",
      label: "Cantidad",
      sortable: true,
      filterable: true,
      filterType: "number",
      minWidth: 70,
      maxWidth: 90,
      priority: 4,
    },
    {
      key: "precio_unit",
      label: "Precio unitario",
      sortable: true,
      filterable: true,
      filterType: "number",
      minWidth: 100,
      maxWidth: 130,
      priority: 5,
      render: (value, row) => {
        const num = parseFloat(value);
        const moneda = monedaMap[row?.orden_id] || "USD";
        const symbol = getCurrencySymbol(moneda);
        return `${symbol}${num.toFixed(2)}`;
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
        ordenId: debouncedFilters.orden_id ? parseInt(debouncedFilters.orden_id) : undefined,
        productoId: debouncedFilters.producto_id ? parseInt(debouncedFilters.producto_id) : undefined,
        cantidadMin: debouncedFilters.cantidad_min ? parseInt(debouncedFilters.cantidad_min) : undefined,
        cantidadMax: debouncedFilters.cantidad_max ? parseInt(debouncedFilters.cantidad_max) : undefined,
        precioUnitMin: debouncedFilters.precio_unit_min ? parseFloat(debouncedFilters.precio_unit_min) : undefined,
        precioUnitMax: debouncedFilters.precio_unit_max ? parseFloat(debouncedFilters.precio_unit_max) : undefined,
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

  // Load currencies for all ordenes in the current view
  useEffect(() => {
    const loadCurrencies = async () => {
      const newMonedaMap: Record<number, string> = {};
      const uniqueOrdenIds = new Set(data.map((detalle) => detalle.orden_id));

      for (const ordenId of uniqueOrdenIds) {
        // Skip if already cached
        if (monedaMap[ordenId]) {
          newMonedaMap[ordenId] = monedaMap[ordenId];
          continue;
        }

        try {
          const response = await fetchOrdenData(ordenId);
          newMonedaMap[ordenId] = response.data.moneda;
        } catch (error) {
          // Default to USD if fetch fails
          newMonedaMap[ordenId] = "USD";
        }
      }

      setMonedaMap((prev) => ({ ...prev, ...newMonedaMap }));
    };

    if (data.length > 0) {
      loadCurrencies();
    }
  }, [data]);

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
        getRowKey={(row) => `orden-detalle-${row.id}`}
      />
    </div>
  );
}
