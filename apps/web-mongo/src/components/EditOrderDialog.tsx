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
import { API_BASE_URL } from "@/lib/env";

/* ----------------------------- Tipos ----------------------------- */
export interface Producto {
  _id: string;
  codigo_mongo: string;
  nombre: string;
  categoria: string;
  equivalencias?: {
    sku: string;
    codigo_alt: string;
  };
}

export interface Item {
  producto_id: string;
  cantidad: number;
  precio_unit: number;
  producto?: Producto;
}

export interface Cliente {
  _id: string;
  nombre: string;
  email: string;
  genero: string;
  pais: string;
  preferencias?: {
    canal: string[];
  };
  creado: string;
}

export interface Orden {
  _id: string;
  cliente_id: string;
  fecha: string;
  canal: "WEB" | "TIENDA";
  moneda: "CRC";
  total: number;
  items: Item[];
  metadatos?: { cupon?: string } | null;
  cliente?: Cliente;
}

const apiBaseUrl = API_BASE_URL;

/* ----------------------------- Props ----------------------------- */
interface EditOrderDialogProps {
  order: Orden;
  open: boolean;
  onClose: () => void;
  onSave: (editedOrder: Orden) => Promise<void>;
}

/* -------------------------- Componente -------------------------- */
export function EditOrderDialog({ order, open, onClose, onSave }: EditOrderDialogProps) {
  const [form, setForm] = useState<Orden>(structuredClone(order));
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (order) setForm(structuredClone(order));
  }, [order]);


  useEffect(() => {
    const fetchData = async () => {
      try {
  // request all clientes (no pagination) so the select shows every client
  const urlClientes = `${apiBaseUrl}/clients`;
        const resClientes = await fetch(urlClientes);
        if (!resClientes.ok) {
          const text = await resClientes.text().catch(() => "");
          console.error("Error fetching clientes", resClientes.status, text);
        } else {
          const ct = resClientes.headers.get("content-type") || "";
          const text = await resClientes.text().catch(() => "");
          let jsonClientes: any = {};
          try {
            jsonClientes = ct.toLowerCase().includes("application/json") ? JSON.parse(text) : JSON.parse(text);
          } catch (e) {
            console.warn("clientes: response not JSON", text.slice(0, 200));
            jsonClientes = {};
          }
          setClientes(jsonClientes.data ?? jsonClientes ?? []);
        }

  // request all products (no pagination) so the select shows every product
  const urlProductos = `${apiBaseUrl}/products?limit=10000`;
        const resProductos = await fetch(urlProductos);
        if (!resProductos.ok) {
          const text = await resProductos.text().catch(() => "");
          console.error("Error fetching products", resProductos.status, text);
        } else {
          const ct = resProductos.headers.get("content-type") || "";
          const text = await resProductos.text().catch(() => "");
          let jsonProductos: any = {};
          try {
            jsonProductos = ct.toLowerCase().includes("application/json") ? JSON.parse(text) : JSON.parse(text);
          } catch (e) {
            console.warn("productos: response not JSON", text.slice(0, 200));
            jsonProductos = {};
          }
          setProductos(jsonProductos.data ?? jsonProductos ?? []);
        }
      } catch (err) {
        console.error("Error cargando datos:", err);
      }
    };

    fetchData();
  }, []);

  // Añadir y eliminar items
  const addItem = () => {
    setForm((prev: Orden) => {
      const items = Array.isArray(prev.items) ? [...prev.items] : [];
      items.push({ producto_id: "", cantidad: 1, precio_unit: 0 });
      return { ...prev, items } as Orden;
    });
  };

  const removeItem = (index: number) => {
    setForm((prev: Orden) => {
      const items = Array.isArray(prev.items) ? [...prev.items] : [];
      if (index >= 0 && index < items.length) items.splice(index, 1);
      return { ...prev, items } as Orden;
    });
  };

  const handleChange = (path: string, value: any) => {
    const parts = path.split(".");
    // If we're changing an items.* field, clone the items array and the specific item so
    // the items identity changes (this ensures effects depending on form.items run).
    if (parts[0] === "items" && parts.length >= 2) {
      const idx = Number(parts[1]);
      const prop = parts[2];
      const items = Array.isArray(form?.items) ? [...form.items] : [];
      const item = items[idx] ? { ...items[idx] } : { producto_id: "", cantidad: 0, precio_unit: 0 };
      if (prop) {
        (item as any)[prop] = value;
      }
      items[idx] = item;
      setForm((prev) => ({ ...(prev as Orden), items } as Orden));
      return;
    }

    // Generic shallow set for other top-level fields
    const partsGen = parts;
    const newForm: any = { ...(form as any) };
    let current: any = newForm;
    for (let i = 0; i < partsGen.length - 1; i++) {
      const key = partsGen[i];
      if (current[key] == null) current[key] = {};
      current = current[key];
    }
    current[partsGen[partsGen.length - 1]] = value;
    setForm(newForm as Orden);
  };

  // Calcular total automáticamente cuando cambian los items
  useEffect(() => {
    try {
      const items = Array.isArray(form?.items) ? form.items : [];
      const total = items.reduce((acc, it) => {
        const qty = Number(it?.cantidad) || 0;
        const pu = Number(it?.precio_unit) || 0;
        return acc + qty * pu;
      }, 0);
      if (form && form.total !== total) {
        setForm((prev) => ({ ...(prev as Orden), total } as Orden));
      }
    } catch (e) {
      // ignore
    }
    // we only care when items array identity/content changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form?.items]);

  const handleSave = async () => {
    // validate before saving
    if (!validate()) return;
    await onSave(form);
    onClose();
  };

  // Basic validation: cliente required, at least one item, each item must have product, qty>0, price>=0
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!form?.cliente_id) {
      newErrors["cliente_id"] = "Cliente requerido";
    }
    const items = Array.isArray(form?.items) ? form.items : [];
    if (items.length === 0) {
      newErrors["items"] = "Agregar al menos un item";
    }
    items.forEach((it, i) => {
      if (!it.producto_id) newErrors[`items.${i}.producto_id`] = "Producto requerido";
      if (!(Number(it.cantidad) > 0)) newErrors[`items.${i}.cantidad`] = "Cantidad debe ser mayor que 0";
      if (!(Number(it.precio_unit) >= 0)) newErrors[`items.${i}.precio_unit`] = "Precio debe ser >= 0";
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isFormValid = useMemo(() => {
    if (!form) return false;
    if (!form.cliente_id) return false;
    const items = Array.isArray(form.items) ? form.items : [];
    if (items.length === 0) return false;
    for (const it of items) {
      if (!it.producto_id) return false;
      if (!(Number(it.cantidad) > 0)) return false;
      if (!(Number(it.precio_unit) >= 0)) return false;
    }
    return true;
  }, [form]);

  // Computed total (sum of cantidad * precio_unit) — shown in UI and used to keep form.total in sync
  const computedTotal = useMemo(() => {
    try {
      const items = Array.isArray(form?.items) ? form.items : [];
      return items.reduce((acc, it) => {
        const qty = Number(it?.cantidad) || 0;
        const pu = Number(it?.precio_unit) || 0;
        return acc + qty * pu;
      }, 0);
    } catch (e) {
      return 0;
    }
  }, [form?.items]);

  // Keep form.total in sync with computedTotal immediately
  useEffect(() => {
    if (!form) return;
    if (form.total !== computedTotal) {
      setForm((prev) => ({ ...(prev as Orden), total: computedTotal } as Orden));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [computedTotal]);

  if (!form) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl rounded-2xl">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold text-center">
        Editar Orden
          </DialogTitle>
        </DialogHeader>

        <ScrollArea className="max-h-[70vh] pr-4">
          {/* --- Información general --- */}
          <Card className="mb-4 border border-neutral-200 dark:border-neutral-800">
            <CardHeader className="text-center">
              <CardTitle className="text-base text-neutral-700 dark:text-neutral-300">
                Información general
              </CardTitle>
            </CardHeader>
          

            <CardContent>
              <div className="mx-auto max-w-2xl grid grid-cols-1 sm:grid-cols-2 gap-6">
                {/* Cliente */}
                <div>
                  <Label className="mb-1.5">Cliente</Label>
                    <Select
                    value={form.cliente_id}
                    onValueChange={(value) => handleChange("cliente_id", value)}
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
                        {form.fecha
                          ? format(new Date(form.fecha), "dd/MM/yyyy")
                          : "Seleccionar fecha"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={form.fecha ? new Date(form.fecha) : undefined}
                        onSelect={(date) => {
                          if (date) handleChange("fecha", date.toISOString());
                        }}
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                {/* Canal */}
                <div>
                  <Label className="mb-1.5">Canal</Label>
                  <Select
                    value={form.canal}
                    onValueChange={(value) => handleChange("canal", value)}
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

          {/* --- Items --- */}
          {Array.isArray(form.items) && form.items.length > 0 && (
            <Card className="mb-2 border border-neutral-200 dark:border-neutral-800">
                  <CardHeader className="flex items-center justify-between">
                    <CardTitle className=" text-neutral-700 dark:text-neutral-300">Items</CardTitle>
                    <Button variant= "outline" size="sm" onClick={addItem} className="ml-2"> Agregar item</Button>
                  </CardHeader>

              <CardContent>
                <div className="mx-auto max-w-2xl space-y-6">
                  {form.items.map((item, i) => (
                    <div key={i} className="grid sm:grid-cols-4 gap-4 border-t pt-4 items-start">
                      {/* Producto */}
                        <div className="sm:col-span-2 min-w-0">
                        <Label className="mb-1">Producto</Label>
            <Select
              value={item.producto_id}
              onValueChange={(value) => handleChange(`items.${i}.producto_id`, value)}
            >
                            <SelectTrigger className="w-full">
                            <SelectValue className="truncate block" placeholder="Seleccionar producto" />
                            </SelectTrigger>
                            <SelectContent>
              {productos.map((p) => (
                <SelectItem key={p._id} value={p._id} className="truncate">
                {p.nombre}
                </SelectItem>
              ))}
                            </SelectContent>
                        </Select>
                        {errors[`items.${i}.producto_id`] && (
                          <p className="text-sm text-red-600 mt-1">{errors[`items.${i}.producto_id`]}</p>
                        )}
                        </div>
                      {/* Cantidad */}
                      <div className="min-w-0">
                        <Label className="mb-1">Cantidad</Label>
                        <Input
                          type="number"
                          value={item.cantidad}
                          onChange={(e) =>
                            handleChange(`items.${i}.cantidad`, Number(e.target.value))
                          }
                          className="w-full"
                        />
                      </div>

                      {/* Precio unitario */}
                      <div className="min-w-0">
                        <Label className="mb-1">Precio Unit</Label>
                        <Input
                          type="number"
                          value={item.precio_unit}
                          onChange={(e) =>
                            handleChange(`items.${i}.precio_unit`, Number(e.target.value))
                          }
                          className="w-full"
                        />
                        {errors[`items.${i}.precio_unit`] && (
                          <p className="text-sm text-red-600 mt-1">{errors[`items.${i}.precio_unit`]}</p>
                        )}
                      </div>

                        {/* Eliminar item */}
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
                </div>
              </CardContent>
            </Card>
          )}
        </ScrollArea>

        <div className="px-6 pb-3 flex items-center justify-between">
          <div className="text-sm text-neutral-700 dark:text-neutral-300">Total calculado</div>
          <div className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">{form?.moneda ?? ""} {computedTotal.toFixed(2)}</div>
        </div>

        <DialogFooter className="flex justify-end gap-3 mt-4">
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button variant="ghost" onClick={handleSave} disabled={!isFormValid} className={`text-white ${!isFormValid ? "opacity-50 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"}`}>
            Guardar cambios
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
