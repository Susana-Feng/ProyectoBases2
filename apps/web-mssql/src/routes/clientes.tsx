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
import { fetchClientes } from "@/lib/api";
import type { Cliente, PaginationMeta } from "@/types/api";

export default function ClientesPage() {
  const [data, setData] = useState<Cliente[]>([]);
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
    Email: "",
    Pais: "",
    Genero: "",
  });

  // Debounce filters to avoid excessive API calls
  const debouncedFilters = useDebounce(filters, 300);

  const columns: ColumnConfig[] = [
    {
      key: "ClienteId",
      label: "Identificador",
      sortable: true,
      minWidth: 60,
      maxWidth: 80,
      priority: 1,
    },
    {
      key: "Nombre",
      label: "Nombre",
      sortable: true,
      filterable: true,
      filterType: "text",
      minWidth: 120,
      maxWidth: 250,
      priority: 2,
    },
    {
      key: "Email",
      label: "Correo electrónico",
      sortable: true,
      filterable: true,
      filterType: "text",
      minWidth: 150,
      maxWidth: 300,
      priority: 3,
    },
    {
      key: "Genero",
      label: "Género",
      sortable: true,
      filterable: true,
      filterType: "select",
      filterOptions: [
        { label: "Masculino", value: "Masculino" },
        { label: "Femenino", value: "Femenino" },
        { label: "Otro", value: "Otro" },
      ],
      minWidth: 80,
      maxWidth: 120,
      priority: 5,
      format: (value) => value || "N/A",
    },
    {
      key: "Pais",
      label: "País",
      sortable: true,
      filterable: true,
      filterType: "text",
      minWidth: 100,
      maxWidth: 150,
      priority: 4,
    },
    {
      key: "FechaRegistro",
      label: "Fecha de registro",
      sortable: true,
      filterable: true,
      filterType: "date",
      minWidth: 120,
      maxWidth: 140,
      priority: 6,
      format: (value) => new Date(value).toLocaleDateString("es-ES"),
    },
  ];


  const loadData = async () => {
    setIsLoading(true);
    try {
      const response = await fetchClientes({
        page: pagination.page,
        limit: pagination.limit,
        sortBy: sortBy,
        sortOrder: sortOrder,
        nombre: debouncedFilters.Nombre || undefined,
        email: debouncedFilters.Email || undefined,
        pais: debouncedFilters.Pais || undefined,
        genero: debouncedFilters.Genero || undefined,
        fechaRegistroDesde: debouncedFilters.FechaRegistro_desde || undefined,
        fechaRegistroHasta: debouncedFilters.FechaRegistro_hasta || undefined,
      });

      setData(response.data);
      setPagination(response.pagination);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Error desconocido";
      toast.error("Error al cargar clientes", {
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
        <h1 className="text-3xl font-bold text-foreground">Clientes</h1>
        <p className="text-muted-foreground mt-2">
          Gestiona y visualiza todos los clientes en la base de datos
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
        getRowKey={(row) => `cliente-${row.ClienteId}`}
      />
    </div>
  );
}
