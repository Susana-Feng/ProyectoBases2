"use client";

import { File, FileSpreadsheet, X } from "lucide-react";
import { useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { uploadExcelFile } from "@/lib/api";
import type { UploadResponse } from "@/types/api";

export default function ExcelUploader() {
  const [uploadState, setUploadState] = useState<{
    file: File | null;
    progress: number;
    uploading: boolean;
    stats?: UploadResponse["stats"];
  }>({
    file: null,
    progress: 0,
    uploading: false,
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validFileTypes = [
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  ];

  const handleFile = async (file: File | undefined) => {
    if (!file) return;

    if (!validFileTypes.includes(file.type)) {
      toast.error("Por favor, sube un archivo CSV, XLSX o XLS.", {
        position: "bottom-right",
        duration: 3000,
      });
      return;
    }

    setUploadState({ file, progress: 0, uploading: true });

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadState((prev) => {
          if (prev.progress >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return { ...prev, progress: prev.progress + Math.random() * 20 };
        });
      }, 200);

      // Upload file to API
      const response = await uploadExcelFile(file);

      clearInterval(progressInterval);
      setUploadState((prev) => ({
        ...prev,
        progress: 100,
        uploading: false,
        stats: response.stats,
      }));

      toast.success(response.message, {
        position: "bottom-right",
        duration: 5000,
        description: `Clientes: ${response.stats.clientesInsertados}, Productos: ${response.stats.productosInsertados}, Órdenes: ${response.stats.ordenesInsertadas}, Detalles: ${response.stats.detallesInsertados}`,
      });
    } catch (error) {
      setUploadState((prev) => ({
        ...prev,
        uploading: false,
      }));

      const errorMessage =
        error instanceof Error ? error.message : "Error desconocido al subir el archivo";
      toast.error("Error al procesar el archivo", {
        position: "bottom-right",
        duration: 5000,
        description: errorMessage,
      });
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFile(event.target.files?.[0]);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    handleFile(event.dataTransfer.files?.[0]);
  };

  const resetFile = () => {
    setUploadState({ file: null, progress: 0, uploading: false });
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const getFileIcon = () => {
    if (!uploadState.file) return <File />;

    const fileExt = uploadState.file.name.split(".").pop()?.toLowerCase() || "";
    return ["csv", "xlsx", "xls"].includes(fileExt) ? (
      <FileSpreadsheet className="h-5 w-5 text-foreground" />
    ) : (
      <File className="h-5 w-5 text-foreground" />
    );
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const { file, progress, uploading, stats } = uploadState;

  return (
    <div className="flex items-center justify-center p-10 w-full max-w-2xl">
      <form className="w-full" onSubmit={(e) => e.preventDefault()}>
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Carga tu archivo Excel
          </h1>
          <p className="text-muted-foreground">
            Sube un archivo Excel con datos de clientes, productos, órdenes y detalles
          </p>
        </div>

        <div
          className="flex justify-center rounded-lg border-2 border-dashed border-input px-6 py-12 bg-muted/30 hover:bg-muted/50 transition-colors cursor-pointer"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <div>
            <File
              className="mx-auto h-12 w-12 text-muted-foreground mb-4"
              aria-hidden={true}
            />
            <div className="flex text-sm leading-6 text-muted-foreground justify-center">
              <p>Arrastra y suelta o</p>
              <label
                htmlFor="file-upload-input"
                className="relative cursor-pointer rounded-sm pl-1 font-medium text-primary hover:underline hover:underline-offset-4"
              >
                <span>selecciona un archivo</span>
                <input
                  id="file-upload-input"
                  name="file-upload-input"
                  type="file"
                  className="sr-only"
                  accept=".csv, .xlsx, .xls"
                  onChange={handleFileChange}
                  ref={fileInputRef}
                  disabled={uploading}
                />
              </label>
            </div>
          </div>
        </div>

        <p className="mt-4 text-xs leading-5 text-muted-foreground flex justify-between">
          <span>Archivos aceptados: CSV, XLSX o XLS</span>
          <span>Máximo: 10MB</span>
        </p>

        {/* Removed example file card */}

        {file && (
          <Card className="relative mt-8 bg-muted p-4 gap-4">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1 h-8 w-8 text-muted-foreground hover:text-foreground"
              aria-label="Remove"
              onClick={resetFile}
              disabled={uploading}
            >
              <X className="h-5 w-5 shrink-0" aria-hidden={true} />
            </Button>

            <div className="flex items-center space-x-2.5">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-sm bg-background shadow-sm ring-1 ring-inset ring-border">
                {getFileIcon()}
              </span>
              <div>
                <p className="text-xs font-medium text-foreground">{file?.name}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {file && formatFileSize(file.size)}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <Progress value={Math.min(progress, 100)} className="h-1.5" />
              <span className="text-xs text-muted-foreground">
                {Math.min(Math.round(progress), 100)}%
              </span>
            </div>

            {stats && (
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="rounded bg-background p-2">
                  <span className="text-muted-foreground">Clientes: </span>
                  <span className="font-semibold">{stats.clientesInsertados}</span>
                </div>
                <div className="rounded bg-background p-2">
                  <span className="text-muted-foreground">Productos: </span>
                  <span className="font-semibold">{stats.productosInsertados}</span>
                </div>
                <div className="rounded bg-background p-2">
                  <span className="text-muted-foreground">Órdenes: </span>
                  <span className="font-semibold">{stats.ordenesInsertadas}</span>
                </div>
                <div className="rounded bg-background p-2">
                  <span className="text-muted-foreground">Detalles: </span>
                  <span className="font-semibold">{stats.detallesInsertados}</span>
                </div>
              </div>
            )}
          </Card>
        )}

        <div className="mt-8 flex items-center justify-end space-x-3">
          <Button
            type="button"
            variant="outline"
            className="whitespace-nowrap"
            onClick={resetFile}
            disabled={!file}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            className="whitespace-nowrap"
            disabled={!file || uploading || progress < 100}
          >
            {uploading ? "Subiendo..." : "Subir"}
          </Button>
        </div>
      </form>
    </div>
  );
}
