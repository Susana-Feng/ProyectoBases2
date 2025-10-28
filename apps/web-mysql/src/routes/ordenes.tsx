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
import { fetchOrdenes, fetchClienteData } from "@/lib/api";
import type { Orden, PaginationMeta } from "@/types/api";

export default function OrdenesPage() {
  const [data, setData] = useState<Orden[]>([]);
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
    cliente_id: "",
    canal: "",
    moneda: "",
  });

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
      key: "cliente_id",
      label: "Cliente",
      sortable: true,
      minWidth: 80,
      maxWidth: 100,
      priority: 2,
      render: (value: number) => (
        <RelatedDataCell
          id={value}
          title="Detalles del cliente"
          fetchFn={fetchClienteData}
          displayFields={[
            { key: "id", label: "Identificador" },
            { key: "nombre", label: "Nombre" },
            { key: "correo", label: "Correo electrónico" },
            { key: "pais", label: "País" },
            { key: "genero", label: "Género" },
            { key: "created_at", label: "Fecha de registro" },
          ]}
        />
      ),
    },
    {
      key: "fecha",
      label: "Fecha",
      sortable: true,
      filterable: true,
      filterType: "date",
      minWidth: 100,
      maxWidth: 120,
      priority: 3,
      format: (value) => new Date(value).toLocaleDateString("es-ES"),
    },
    {
      key: "canal",
      label: "Canal",
      sortable: true,
      filterable: true,
      filterType: "text",
      minWidth: 80,
      maxWidth: 120,
      priority: 4,
    },
    {
      key: "moneda",
      label: "Moneda",
      sortable: true,
      filterable: true,
      filterType: "select",
      filterOptions: [
        { label: "USD", value: "USD" },
        { label: "CRC", value: "CRC" },
      ],
      minWidth: 70,
      maxWidth: 90,
      priority: 6,
    },
    {
      key: "total",
      label: "Total",
      sortable: true,
      filterable: true,
      filterType: "number",
      minWidth: 90,
      maxWidth: 120,
      priority: 5,
      render: (value, row) => {
        const num = parseFloat(value);
        const symbol = getCurrencySymbol(row?.moneda);
        return `${symbol}${num.toFixed(2)}`;
      },
    },
  ];


  const loadData = async () => {
    setIsLoading(true);
    try {
      const response = await fetchOrdenes({
        page: pagination.page,
        limit: pagination.limit,
        sortBy: sortBy,
        sortOrder: sortOrder,
        clienteId: debouncedFilters.cliente_id ? parseInt(debouncedFilters.cliente_id) : undefined,
        canal: debouncedFilters.canal || undefined,
        moneda: debouncedFilters.moneda || undefined,
        fechaDesde: debouncedFilters.fecha_desde || undefined,
        fechaHasta: debouncedFilters.fecha_hasta || undefined,
        totalMin: debouncedFilters.total_min ? parseFloat(debouncedFilters.total_min) : undefined,
        totalMax: debouncedFilters.total_max ? parseFloat(debouncedFilters.total_max) : undefined,
      });

      setData(response.data);
      setPagination(response.pagination);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Error desconocido";
      toast.error("Error al cargar órdenes", {
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
        <h1 className="text-3xl font-bold text-foreground">Órdenes</h1>
        <p className="text-muted-foreground mt-2">
          Gestiona y visualiza todas las órdenes en la base de datos
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
        getRowKey={(row) => `orden-${row.id}`}
      />
    </div>
  );
}
