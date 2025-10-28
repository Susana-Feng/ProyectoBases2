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
import { fetchProductos } from "@/lib/api";
import type { Producto, PaginationMeta } from "@/types/api";

export default function ProductosPage() {
  const [data, setData] = useState<Producto[]>([]);
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
    Nombre: "",
    SKU: "",
    Categoria: "",
  });

  // Debounce filters to avoid excessive API calls
  const debouncedFilters = useDebounce(filters, 300);

  const columns: ColumnConfig[] = [
    {
      key: "ProductoId",
      label: "ID",
      sortable: true,
      minWidth: 60,
      maxWidth: 80,
      priority: 1,
    },
    {
      key: "SKU",
      label: "SKU",
      sortable: true,
      filterable: true,
      minWidth: 100,
      maxWidth: 150,
      priority: 3,
    },
    {
      key: "Nombre",
      label: "Nombre",
      sortable: true,
      filterable: true,
      minWidth: 150,
      maxWidth: 300,
      priority: 2,
    },
    {
      key: "Categoria",
      label: "Categoría",
      sortable: true,
      filterable: true,
      minWidth: 120,
      maxWidth: 180,
      priority: 4,
    },
  ];


  const loadData = async () => {
    setIsLoading(true);
    try {
      const response = await fetchProductos({
        page: pagination.page,
        limit: pagination.limit,
        sortBy: sortBy,
        sortOrder: sortOrder,
        nombre: debouncedFilters.Nombre || undefined,
        sku: debouncedFilters.SKU || undefined,
        categoria: debouncedFilters.Categoria || undefined,
      });

      setData(response.data);
      setPagination(response.pagination);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Error desconocido";
      toast.error("Error al cargar productos", {
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
        <h1 className="text-3xl font-bold text-foreground">Productos</h1>
        <p className="text-muted-foreground mt-2">
          Gestiona y visualiza todos los productos en la base de datos
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
        getRowKey={(row) => `producto-${row.ProductoId}`}
      />
    </div>
  );
}
