import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ExternalLink } from "lucide-react";
import { toast } from "sonner";

interface RelatedDataCellProps {
  id: number;
  title: string;
  fetchFn: (id: number) => Promise<any>;
  displayFields: { key: string; label: string; format?: (value: any) => string }[];
}

export function RelatedDataCell({
  id,
  title,
  fetchFn,
  displayFields,
}: RelatedDataCellProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleOpenDialog = async () => {
    setIsOpen(true);

    // Only fetch if we don't have data cached
    if (data || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetchFn(id);
      if (response.success) {
        setData(response.data);
      } else {
        throw new Error(response.message || "Error al cargar los datos");
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Error desconocido";
      setError(errorMessage);
      toast.error("Error al cargar datos", {
        description: errorMessage,
        position: "bottom-right",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleOpenDialog}
        className="gap-2"
      >
        <span className="font-mono text-xs">{id}</span>
        <ExternalLink className="h-3 w-3" />
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            <DialogDescription>ID: {id}</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {isLoading ? (
              <div className="space-y-3">
                {displayFields.map((field) => (
                  <div key={field.key}>
                    <Skeleton className="h-4 w-20 mb-1" />
                    <Skeleton className="h-6 w-full" />
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="p-4 bg-destructive/10 text-destructive rounded-md text-sm">
                {error}
              </div>
            ) : data ? (
              <div className="space-y-3">
                {displayFields.map((field) => {
                  const value = data[field.key];
                  const displayValue = field.format
                    ? field.format(value)
                    : String(value || "-");

                  return (
                    <div key={field.key}>
                      <label className="text-sm font-medium text-muted-foreground">
                        {field.label}
                      </label>
                      <div className="mt-1 text-sm font-medium wrap-break-word">
                        {field.key === "Fecha" ||
                        field.key === "FechaRegistro" ? (
                          <Badge variant="outline">
                            {new Date(value).toLocaleDateString("es-ES", {
                              year: "numeric",
                              month: "short",
                              day: "numeric",
                            })}
                          </Badge>
                        ) : field.key === "Email" ? (
                          <a
                            href={`mailto:${value}`}
                            className="text-primary hover:underline"
                          >
                            {value}
                          </a>
                        ) : (
                          displayValue
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
