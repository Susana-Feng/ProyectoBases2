import { useState, useEffect, useMemo } from "react";
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ArrowUpDown, Filter, X, ArrowUp, ArrowDown, Settings2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { PaginationMeta } from "@/types/api";


export interface ColumnConfig {
  key: string;
  label: string;
  sortable?: boolean;
  filterable?: boolean;
  format?: (value: any) => string;
  width?: string;
  minWidth?: number; // in pixels
  maxWidth?: number; // in pixels
  priority?: number; // 1 = highest priority, higher numbers = lower priority
}

interface DataTableProps {
  columns: ColumnConfig[];
  data: any[];
  pagination: PaginationMeta;
  isLoading: boolean;
  onPageChange: (page: number) => void;
  onLimitChange: (limit: number) => void;
  onSort?: (sortBy: string, sortOrder: "asc" | "desc") => void;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  filters?: Record<string, string>;
  onFilterChange?: (key: string, value: string) => void;
  getRowKey?: (row: any, index: number) => string;
}

export function DataTable({
  columns,
  data,
  pagination,
  isLoading,
  onPageChange,
  onLimitChange,
  onSort,
  sortBy,
  sortOrder,
  filters = {},
  onFilterChange,
  getRowKey,
}: DataTableProps) {
  const [localPage, setLocalPage] = useState(pagination.page);
  const [openFilterColumn, setOpenFilterColumn] = useState<string | null>(null);
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const [visibleColumns, setVisibleColumns] = useState<Record<string, boolean>>(() => {
    // Initialize all columns as visible
    const initial: Record<string, boolean> = {};
    columns.forEach(col => {
      initial[col.key] = true;
    });
    return initial;
  });
  const [showColumnSelector, setShowColumnSelector] = useState(false);


  useEffect(() => {
    setLocalPage(pagination.page);
  }, [pagination.page]);

  // Calculate optimal column widths based on content (only for visible columns)
  useEffect(() => {
    if (data.length === 0) return;

    const newWidths: Record<string, number> = {};
    
    columns.forEach((column) => {
      if (!visibleColumns[column.key]) return; // Skip hidden columns
      
      // Calculate width based on header and content
      const headerLength = column.label.length;
      const maxContentLength = Math.max(
        ...data.slice(0, 10).map((row) => { // Only check first 10 rows for performance
          const value = column.format 
            ? column.format(row[column.key])
            : String(row[column.key] || "");
          return value.length;
        }),
        headerLength
      );

      // Base width calculation (roughly 8px per character + padding)
      let calculatedWidth = Math.max(maxContentLength * 8 + 32, 80);
      
      // Apply min/max constraints
      if (column.minWidth) {
        calculatedWidth = Math.max(calculatedWidth, column.minWidth);
      }
      if (column.maxWidth) {
        calculatedWidth = Math.min(calculatedWidth, column.maxWidth);
      }

      newWidths[column.key] = calculatedWidth;
    });

    setColumnWidths(newWidths);
  }, [data, columns, visibleColumns]);


  const clearFilter = (columnKey: string) => {
    if (onFilterChange) {
      onFilterChange(columnKey, "");
    }
  };

  const toggleColumnVisibility = (columnKey: string) => {
    setVisibleColumns(prev => ({
      ...prev,
      [columnKey]: !prev[columnKey]
    }));
  };

  const toggleSortOrder = () => {
    if (onSort && sortBy) {
      const newOrder = sortOrder === "asc" ? "desc" : "asc";
      onSort(sortBy, newOrder);
    }
  };

  const clearSort = () => {
    if (onSort) {
      onSort("", "asc");
    }
  };

  const handleFirstPage = () => {
    setLocalPage(1);
    onPageChange(1);
  };

  const handlePreviousPage = () => {
    const newPage = Math.max(1, localPage - 1);
    setLocalPage(newPage);
    onPageChange(newPage);
  };

  const handleNextPage = () => {
    const newPage = Math.min(pagination.totalPages, localPage + 1);
    setLocalPage(newPage);
    onPageChange(newPage);
  };

  const handleLastPage = () => {
    setLocalPage(pagination.totalPages);
    onPageChange(pagination.totalPages);
  };

  const handleLimitChange = (value: string) => {
    onLimitChange(parseInt(value));
    setLocalPage(1);
    onPageChange(1);
  };

  // Memoize table headers to prevent unnecessary re-renders (only visible columns)
  const tableHeaders = useMemo(
    () =>
      columns
        .filter(column => visibleColumns[column.key])
        .map((column) => {
          const hasFilter = filters[column.key] && filters[column.key].trim() !== "";
          const width = columnWidths[column.key];
          
          return (
            <TableHead
              key={column.key}
              className={`${
                column.filterable ? "cursor-pointer hover:bg-muted select-none" : ""
              } transition-all duration-300 ease-in-out`}
              style={{ 
                width: width ? `${width}px` : 'auto',
                minWidth: width ? `${width}px` : 'auto'
              }}
            >
              {column.filterable ? (
                <Popover
                  open={openFilterColumn === column.key}
                  onOpenChange={(open) => setOpenFilterColumn(open ? column.key : null)}
                >
                  <PopoverTrigger asChild>
                    <div className="flex items-center gap-2">
                      <span className="truncate">{column.label}</span>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {hasFilter && (
                          <div className="w-2 h-2 bg-primary rounded-full"></div>
                        )}
                        <Filter className="h-3 w-3 text-muted-foreground" />
                      </div>
                    </div>
                  </PopoverTrigger>
                  <PopoverContent className="w-64 p-3" align="start">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Filtrar {column.label}</span>
                        {hasFilter && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => clearFilter(column.key)}
                            className="h-6 w-6 p-0"
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                      <Input
                        placeholder={`Buscar ${column.label.toLowerCase()}...`}
                        value={filters[column.key] || ""}
                        onChange={(e) => {
                          if (onFilterChange) {
                            onFilterChange(column.key, e.target.value);
                          }
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            setOpenFilterColumn(null);
                          }
                        }}
                        className="h-8"
                        autoFocus
                      />
                    </div>
                  </PopoverContent>
                </Popover>
              ) : (
                <span className="truncate">{column.label}</span>
              )}
            </TableHead>
          );
        }),
    [columns, visibleColumns, filters, openFilterColumn, onFilterChange, columnWidths]
  );



  // Memoize table rows to prevent unnecessary re-renders (only visible columns)
  const tableRows = useMemo(() => {
    const visibleColumnsArray = columns.filter(column => visibleColumns[column.key]);
    
    // If loading and no data yet, show skeletons
    if (isLoading && data.length === 0) {
      return Array(5)
        .fill(0)
        .map((_, i) => (
          <TableRow key={`skeleton-${i}`} className="h-12">
            {visibleColumnsArray.map((column) => (
              <TableCell key={column.key}>
                <Skeleton className="h-4 w-full" />
              </TableCell>
            ))}
          </TableRow>
        ));
    }

    // If no data and not loading, show empty state
    if (data.length === 0 && !isLoading) {
      return (
        <TableRow className="h-12">
          <TableCell
            colSpan={visibleColumnsArray.length}
            className="text-center py-8 text-muted-foreground"
          >
            No hay datos disponibles
          </TableCell>
        </TableRow>
      );
    }

    // Show actual data (loading overlay will be shown on top if needed)
    return data.map((row, i) => {
      const rowKey = getRowKey ? getRowKey(row, i) : `row-${i}`;
      return (
        <TableRow key={rowKey} className="hover:bg-muted/30 h-12">
          {visibleColumnsArray.map((column) => {
            const value = column.format
              ? column.format(row[column.key])
              : String(row[column.key] || "");
            const width = columnWidths[column.key];
            const shouldTruncate = width && value.length * 8 > width - 32; // Account for padding
            
            return (
              <TableCell 
                key={column.key} 
                className="transition-all duration-300 ease-in-out"
                style={{ 
                  width: width ? `${width}px` : 'auto',
                  minWidth: width ? `${width}px` : 'auto'
                }}
              >
                {shouldTruncate ? (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className="text-sm block truncate cursor-help">
                          {value}
                        </span>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-xs">
                        <p className="break-words">{value}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                ) : (
                  <span className="text-sm block">
                    {value}
                  </span>
                )}
              </TableCell>
            );
          })}
        </TableRow>
      );
    });
  }, [data, columns, visibleColumns, isLoading, getRowKey, columnWidths]);

  return (
    <div className="space-y-4">
      {/* Controls row */}
      <div className="flex items-center justify-between">
        {/* Left side - Sort controls */}
        <div className="flex items-center gap-2">
          {onSort && (
            <>
              <Select 
                value={sortBy || ''} 
                onValueChange={(value) => {
                  if (value && onSort) {
                    onSort(value, sortOrder || 'asc');
                  }
                }}
              >
                <SelectTrigger className="w-48">
                  <ArrowUpDown className="h-4 w-4 mr-2 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <SelectValue placeholder="Ordenar por..." className="block truncate text-left" />
                  </div>
                </SelectTrigger>
                <SelectContent>
                  {columns
                    .filter(col => col.sortable)
                    .map((column) => (
                      <SelectItem key={column.key} value={column.key}>
                        {column.label}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
              
              {sortBy && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={toggleSortOrder}
                    className="h-9 px-3"
                    title={`Cambiar a orden ${sortOrder === "asc" ? "descendente" : "ascendente"}`}
                  >
                    {sortOrder === "asc" ? (
                      <ArrowUp className="h-4 w-4" />
                    ) : (
                      <ArrowDown className="h-4 w-4" />
                    )}
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={clearSort}
                    className="h-9 px-3"
                    title="Limpiar ordenamiento"
                  >
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                </>
              )}
            </>
          )}
        </div>

        {/* Right side - Column visibility */}
        <DropdownMenu open={showColumnSelector} onOpenChange={setShowColumnSelector}>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="h-9 gap-2">
              <Settings2 className="h-4 w-4" />
              Ver
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="flex items-center justify-between">
              <span>Columnas visibles</span>
              <span className="text-xs text-muted-foreground font-normal">
                {Object.values(visibleColumns).filter(Boolean).length} de {columns.length}
              </span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {columns.map((column) => (
              <DropdownMenuCheckboxItem
                key={column.key}
                className="capitalize"
                checked={visibleColumns[column.key]}
                onCheckedChange={() => {
                  // Prevent the dropdown from closing
                  toggleColumnVisibility(column.key);
                }}
                onSelect={(e) => {
                  // Prevent the dropdown from closing when clicking
                  e.preventDefault();
                }}
              >
                {column.label}
              </DropdownMenuCheckboxItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-hidden relative">
        <Table style={{ tableLayout: 'fixed', width: '100%' }}>
          <TableHeader>
            <TableRow className="bg-muted/50">
              {tableHeaders}
            </TableRow>
          </TableHeader>
          <TableBody className="min-h-[400px]">
            {tableRows}
          </TableBody>
        </Table>

        {/* Loading overlay */}
        {isLoading && data.length > 0 && (
          <div className="absolute inset-0 bg-background/50 backdrop-blur-[1px] flex items-center justify-center">
            <div className="flex items-center gap-2 text-muted-foreground">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent"></div>
              <span className="text-sm">Cargando...</span>
            </div>
          </div>
        )}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4">
        {/* Left side - Showing count */}
        <div className="text-sm text-muted-foreground">
          Mostrando {data.length} de {pagination.total} registros
        </div>

        {/* Right side - Pagination controls */}
        <div className="flex items-center gap-4">
          {/* Rows per page selector */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Filas por página:</span>
            <Select value={String(pagination.limit)} onValueChange={handleLimitChange}>
              <SelectTrigger className="w-20 h-8 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[10, 20, 50, 100].map((limit) => (
                  <SelectItem key={limit} value={String(limit)}>
                    {limit}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Page info */}
          <div className="text-sm text-muted-foreground whitespace-nowrap">
            Página {pagination.page} de {pagination.totalPages}
          </div>

          {/* Navigation buttons */}
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={handleFirstPage}
              disabled={pagination.page === 1 || isLoading}
              className="h-8 w-8 p-0"
            >
              <ChevronsLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handlePreviousPage}
              disabled={pagination.page === 1 || isLoading}
              className="h-8 w-8 p-0"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleNextPage}
              disabled={pagination.page >= pagination.totalPages || isLoading}
              className="h-8 w-8 p-0"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleLastPage}
              disabled={pagination.page >= pagination.totalPages || isLoading}
              className="h-8 w-8 p-0"
            >
              <ChevronsRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
