import { useState, useEffect, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { CalendarIcon } from "lucide-react";
import { format } from "date-fns";

import type { Orden, Cliente, Producto, Item } from "./EditOrderDialog"; // importa los tipos si están allí

const apiBaseUrl =
  (import.meta?.env?.VITE_API_BASE as string) || "http://localhost:8000";

interface CreateOrderDialogProps {
  open: boolean;
  onClose: () => void;
  onCreate: (newOrder: Orden) => Promise<void>;
}

export function CreateOrderDialog({ open, onClose, onCreate }: CreateOrderDialogProps) {
  const [form, setForm] = useState<Orden>({
    _id: "",
    cliente_id: "",
    fecha: new Date().toISOString(),
    canal: "WEB",
    moneda: "CRC",
    total: 0,
    items: [],
    metadatos: null,
  });

  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  /* ----------------------------- Cargar datos ----------------------------- */
  useEffect(() => {
    const fetchData = async () => {
      try {
        const resClientes = await fetch(`${apiBaseUrl}/clientes`);
        const clientesJson = await resClientes.json();
        setClientes(clientesJson.data ?? clientesJson ?? []);

        const resProductos = await fetch(`${apiBaseUrl}/productos`);
        const productosJson = await resProductos.json();
        setProductos(productosJson.data ?? productosJson ?? []);
      } catch (err) {
        console.error("Error cargando datos:", err);
      }
    };
    fetchData();
  }, []);

  /* ----------------------------- Funciones auxiliares ----------------------------- */

  const addItem = () => {
    setForm((prev) => ({
      ...prev,
      items: [...(prev.items || []), { producto_id: "", cantidad: 1, precio_unit: 0 }],
    }));
  };

  const removeItem = (index: number) => {
    setForm((prev) => {
      const items = [...(prev.items || [])];
      items.splice(index, 1);
      return { ...prev, items };
    });
  };

  const handleChange = (path: string, value: any) => {
    const parts = path.split(".");
    if (parts[0] === "items" && parts.length >= 3) {
      const idx = Number(parts[1]);
      const prop = parts[2];
      const items = [...(form.items || [])];
      const item = { ...items[idx], [prop]: value };
      items[idx] = item;
      setForm((prev) => ({ ...prev, items }));
      return;
    }

    setForm((prev) => {
      const newForm: any = { ...prev };
      let current = newForm;
      for (let i = 0; i < parts.length - 1; i++) {
        const key = parts[i];
        if (!current[key]) current[key] = {};
        current = current[key];
      }
      current[parts[parts.length - 1]] = value;
      return newForm;
    });
  };

  /* ----------------------------- Cálculo automático del total ----------------------------- */
  const computedTotal = useMemo(() => {
    return (form.items || []).reduce(
      (acc, it) => acc + (Number(it.cantidad) || 0) * (Number(it.precio_unit) || 0),
      0
    );
  }, [form.items]);

  useEffect(() => {
    if (form.total !== computedTotal) {
      setForm((prev) => ({ ...prev, total: computedTotal }));
    }
  }, [computedTotal]);

  /* ----------------------------- Validación ----------------------------- */
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!form.cliente_id) newErrors["cliente_id"] = "Cliente requerido";
    if (!form.items.length) newErrors["items"] = "Debe agregar al menos un item";
    form.items.forEach((it, i) => {
      if (!it.producto_id) newErrors[`items.${i}.producto_id`] = "Producto requerido";
      if (!(Number(it.cantidad) > 0)) newErrors[`items.${i}.cantidad`] = "Cantidad > 0";
      if (!(Number(it.precio_unit) >= 0)) newErrors[`items.${i}.precio_unit`] = "Precio >= 0";
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isFormValid = useMemo(() => validate(), [form]);

  /* ----------------------------- Guardar ----------------------------- */
  const handleCreate = async () => {
    if (!validate()) return;
    await onCreate(form);
    onClose();
  };

  /* ----------------------------- Render ----------------------------- */
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl rounded-2xl">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold text-center">
            Crear Nueva Orden
          </DialogTitle>
        </DialogHeader>

        <ScrollArea className="max-h-[70vh] pr-4">
          <Card className="mb-4 border border-neutral-200 dark:border-neutral-800">
            <CardHeader>
              <CardTitle className="text-base text-center">Información General</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mx-auto max-w-2xl grid grid-cols-1 sm:grid-cols-2 gap-6">
                {/* Cliente */}
                <div>
                  <Label className="mb-1.5">Cliente</Label>
                  <Select
                    value={form.cliente_id}
                    onValueChange={(v) => handleChange("cliente_id", v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar cliente" />
                    </SelectTrigger>
                    <SelectContent>
                      {clientes.map((c) => (
                        <SelectItem key={c._id} value={c._id}>
                          {c.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors["cliente_id"] && (
                    <p className="text-sm text-red-600 mt-1">{errors["cliente_id"]}</p>
                  )}
                </div>

                {/* Fecha */}
                <div>
                  <Label className="mb-1.5">Fecha</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-left font-normal"
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {form.fecha ? format(new Date(form.fecha), "dd/MM/yyyy") : "Seleccionar"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={form.fecha ? new Date(form.fecha) : undefined}
                        onSelect={(date) =>
                          date && handleChange("fecha", date.toISOString())
                        }
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                {/* Canal */}
                <div>
                  <Label className="mb-1.5">Canal</Label>
                  <Select
                    value={form.canal}
                    onValueChange={(v) => handleChange("canal", v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar canal" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="WEB">WEB</SelectItem>
                      <SelectItem value="TIENDA">TIENDA</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Items */}
          <Card className="mb-4 border border-neutral-200 dark:border-neutral-800">
            <CardHeader className="flex items-center justify-between">
              <CardTitle className="text-neutral-700 dark:text-neutral-300">
                Items
              </CardTitle>
              <Button variant="outline" size="sm" onClick={addItem}>
                Agregar Item
              </Button>
            </CardHeader>
            <CardContent>
              {form.items.length === 0 && (
                <p className="text-sm text-neutral-500">No hay items agregados.</p>
              )}
              {form.items.map((item, i) => (
                <div key={i} className="grid sm:grid-cols-4 gap-4 border-t pt-4 items-start">
                  {/* Producto */}
                  <div className="sm:col-span-2">
                    <Label>Producto</Label>
                    <Select
                      value={item.producto_id}
                      onValueChange={(v) => handleChange(`items.${i}.producto_id`, v)}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Seleccionar producto" />
                      </SelectTrigger>
                      <SelectContent>
                        {productos.map((p) => (
                          <SelectItem key={p._id} value={p._id}>
                            {p.nombre}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Cantidad */}
                  <div>
                    <Label>Cantidad</Label>
                    <Input
                      type="number"
                      value={item.cantidad}
                      onChange={(e) =>
                        handleChange(`items.${i}.cantidad`, Number(e.target.value))
                      }
                    />
                  </div>

                  {/* Precio unit */}
                  <div>
                    <Label>Precio Unit</Label>
                    <Input
                      type="number"
                      value={item.precio_unit}
                      onChange={(e) =>
                        handleChange(`items.${i}.precio_unit`, Number(e.target.value))
                      }
                    />
                  </div>

                  {/* Eliminar */}
                  <div className="flex items-center">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => removeItem(i)}
                    >
                      Eliminar
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </ScrollArea>

        {/* Total */}
        <div className="px-6 pb-3 flex items-center justify-between">
          <div className="text-sm text-neutral-700 dark:text-neutral-300">
            Total calculado
          </div>
          <div className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            {form.moneda} {computedTotal.toFixed(2)}
          </div>
        </div>

        {/* Botones */}
        <DialogFooter className="flex justify-end gap-3 mt-4">
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            onClick={handleCreate}
            disabled={!isFormValid}
            className={`text-white ${!isFormValid ? "opacity-50 cursor-not-allowed" : "bg-green-600 hover:bg-green-700"}`}
          >
            Crear Orden
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
