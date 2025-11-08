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


// Tipos basados en Orders.tsx
interface Producto {
  producto_id: string;
  sku: string | null;
  nombre: string;
  categoria: string;
}

interface Cliente {
  cliente_id: string;
  nombre: string;
  email: string | null;
  genero: 'M' | 'F';
  pais: string;
  fecha_registro: string;
}

// En Orders.tsx
interface Orden {
  orden_id?: string; // Cambiar a opcional
  cliente: {
    cliente_id: string;
    nombre: string;
  };
  fecha: string;
  canal: string;
  moneda: string;
  total: number;
  items: {
    producto_id: string;
    cantidad: number;
    precio_unitario: number;
    producto?: {
      producto_id: string;
      nombre: string;
    };
  }[];
}

// URLs de Supabase
const apiBaseUrl = "http://localhost:8000/api/supabase/";
const clientesUrl = `${apiBaseUrl}clients/`;
const productosUrl = `${apiBaseUrl}products/`;

// Headers de Supabase
const supabaseHeaders = {
  "apikey": import.meta.env.VITE_SUPABASE_ANON_KEY,
  "Authorization": `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`,
  "Content-Type": "application/json"
};

interface CreateOrderDialogProps {
  open: boolean;
  onClose: () => void;
  onCreate: (newOrder: Orden) => Promise<void>;
}

async function fetchJson(url: string, method: string = "GET", payload?: any) {
  const res = await fetch(url, {
    method,
    headers: supabaseHeaders,
    body: payload ? JSON.stringify(payload) : undefined
  });
  if (!res.ok) throw new Error(`${url} -> HTTP ${res.status}`);
  return res.json();
}

export function CreateOrderDialog({ open, onClose, onCreate }: CreateOrderDialogProps) {
  const [form, setForm] = useState<Omit<Orden, 'orden_id'>>({
    cliente: {
      cliente_id: "",
      nombre: ""
    },
    fecha: new Date().toISOString(),
    canal: "WEB",
    moneda: "USD",
    total: 0,
    items: [],
  });

  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [localLoading, setLocalLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  /* ----------------------------- Cargar datos ----------------------------- */
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Cargar clientes desde Supabase
        const clientesData = await fetchJson(clientesUrl);
        console.log('👥 Clientes cargados:', clientesData);
        setClientes(Array.isArray(clientesData) ? clientesData : []);

        // Cargar productos desde Supabase
        const productosData = await fetchJson(productosUrl);
        console.log('📦 Productos cargados:', productosData);
        setProductos(Array.isArray(productosData) ? productosData : []);
      } catch (err) {
        console.error("Error cargando datos:", err);
        setLocalError("Error cargando datos de clientes y productos");
      }
    };

    if (open) {
      fetchData();
      // Resetear form cuando se abre
      setForm({
        cliente: {
          cliente_id: "",
          nombre: ""
        },
        fecha: new Date().toISOString(),
        canal: "WEB",
        moneda: "USD",
        total: 0,
        items: [],
      });
      setErrors({});
      setLocalError(null);
    }
  }, [open]);

  /* ----------------------------- Funciones auxiliares ----------------------------- */

  const addItem = () => {
    setForm((prev) => ({
      ...prev,
      items: [...prev.items, { 
        producto_id: "", 
        cantidad: 1, 
        precio_unitario: 0 
      }],
    }));
  };

  const removeItem = (index: number) => {
    setForm((prev) => {
      const items = [...prev.items];
      items.splice(index, 1);
      return { ...prev, items };
    });
  };

  const handleChange = (path: string, value: any) => {
    const parts = path.split(".");
    
    // Manejar cambios en items
    if (parts[0] === "items" && parts.length >= 3) {
      const idx = Number(parts[1]);
      const prop = parts[2];
      const items = [...form.items];
      const item = { ...items[idx], [prop]: value };
      
      // Si cambiamos producto_id, actualizar también el objeto producto
      if (prop === "producto_id") {
        const producto = productos.find(p => p.producto_id === value);
        if (producto) {
          item.producto = {
            nombre: producto.nombre,
            producto_id: producto.producto_id
          };
        }
      }
      
      items[idx] = item;
      setForm((prev) => ({ ...prev, items }));
      return;
    }

    // Manejar cambios en cliente
    if (parts[0] === "cliente" && parts.length === 2) {
      const prop = parts[1];
      const newCliente = { ...form.cliente, [prop]: value };
      
      // Si cambiamos cliente_id, actualizar también el nombre del cliente
      if (prop === "cliente_id") {
        const cliente = clientes.find(c => c.cliente_id === value);
        if (cliente) {
          newCliente.nombre = cliente.nombre;
        }
      }
      
      setForm(prev => ({ ...prev, cliente: newCliente }));
      return;
    }

    // Cambios en campos de nivel superior
    setForm((prev) => ({ ...prev, [path]: value }));
  };

  /* ----------------------------- Cálculo automático del total ----------------------------- */
  const computedTotal = useMemo(() => {
    return form.items.reduce(
      (acc, it) => acc + (Number(it.cantidad) || 0) * (Number(it.precio_unitario) || 0),
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
    if (!form.cliente.cliente_id) {
      newErrors["cliente_id"] = "Cliente requerido";
    }
    if (form.items.length === 0) {
      newErrors["items"] = "Debe agregar al menos un item";
    }
    form.items.forEach((it, i) => {
      if (!it.producto_id) newErrors[`items.${i}.producto_id`] = "Producto requerido";
      if (!(Number(it.cantidad) > 0)) newErrors[`items.${i}.cantidad`] = "Cantidad > 0";
      if (!(Number(it.precio_unitario) >= 0)) newErrors[`items.${i}.precio_unitario`] = "Precio >= 0";
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isFormValid = useMemo(() => {
    if (!form.cliente.cliente_id) return false;
    if (form.items.length === 0) return false;
    
    for (const it of form.items) {
      if (!it.producto_id) return false;
      if (!(Number(it.cantidad) > 0)) return false;
      if (!(Number(it.precio_unitario) >= 0)) return false;
    }
    
    return true;
  }, [form]);

  /* ----------------------------- Guardar ----------------------------- */
  const handleCreate = async () => {
    if (!validate()) return;
    
    setLocalLoading(true);
    setLocalError(null);
    
    try {
      const orderData: Orden = {
        orden_id: "",
        cliente: {
          cliente_id: form.cliente.cliente_id,
          nombre: form.cliente.nombre
        },
        fecha: form.fecha,
        canal: form.canal,
        moneda: form.moneda,
        total: computedTotal,
        items: form.items.map(item => ({
          producto_id: item.producto_id,
          cantidad: item.cantidad,
          precio_unitario: item.precio_unitario,
          producto: item.producto
        }))
      };

      console.log('📤 Creando orden:', orderData);
      await onCreate(orderData);
      onClose();
    } catch (error: any) {
      console.error('Error creando orden:', error);
      setLocalError(error.message || 'Error al crear orden');
    } finally {
      setLocalLoading(false);
    }
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
          {localError && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {localError}
            </div>
          )}

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
                    value={form.cliente.cliente_id}
                    onValueChange={(v) => handleChange("cliente.cliente_id", v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar cliente">
                        {form.cliente.nombre || "Seleccionar cliente"}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {clientes.map((c) => (
                        <SelectItem key={c.cliente_id} value={c.cliente_id}>
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
                      <SelectItem value="APP">APP</SelectItem>
                      <SelectItem value="PARTNER">PARTNER</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Moneda */}
                <div>
                  <Label className="mb-1.5">Moneda</Label>
                  <Select
                    value={form.moneda}
                    onValueChange={(v) => handleChange("moneda", v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar moneda" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="USD">USD</SelectItem>
                      <SelectItem value="CRC">CRC</SelectItem>
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
              <Button variant="outline" size="sm" onClick={addItem} disabled={localLoading}>
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
                  <div className="sm:col-span-2 min-w-0">
                    <Label className= "mb-2">Producto</Label>
                    <Select
                      value={item.producto_id}
                      onValueChange={(v) => handleChange(`items.${i}.producto_id`, v)}
                      disabled={localLoading}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue className="truncate block">
                          {item.producto?.nombre || "Seleccionar producto"}
                        </SelectValue>
                      </SelectTrigger>
                      <SelectContent>
                        {productos.map((p) => (
                          <SelectItem key={p.producto_id} value={p.producto_id} className="truncate">
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
                    <Label className= "mb-2">Cantidad</Label>
                    <Input
                      type="number"
                      min="1"
                      value={item.cantidad}
                      onChange={(e) =>
                        handleChange(`items.${i}.cantidad`, Number(e.target.value))
                      }
                      disabled={localLoading}
                    />
                    {errors[`items.${i}.cantidad`] && (
                      <p className="text-sm text-red-600 mt-1">{errors[`items.${i}.cantidad`]}</p>
                    )}
                  </div>

                  {/* Precio unitario */}
                  <div className="min-w-0">
                    <Label className= "mb-2 ">Precio Unit</Label>
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.precio_unitario}
                      onChange={(e) =>
                        handleChange(`items.${i}.precio_unitario`, Number(e.target.value))
                      }
                      disabled={localLoading}
                    />
                    {errors[`items.${i}.precio_unitario`] && (
                      <p className="text-sm text-red-600 mt-1">{errors[`items.${i}.precio_unitario`]}</p>
                    )}
                  </div>

                  {/* Eliminar */}
                  <div className="flex items-center">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => removeItem(i)}
                      disabled={localLoading}
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
          <Button variant="outline" onClick={onClose} disabled={localLoading}>
            Cancelar
          </Button>
          <Button
            onClick={handleCreate}
            disabled={!isFormValid || localLoading}
            className={`text-white ${!isFormValid || localLoading ? "opacity-50 cursor-not-allowed" : "bg-green-600 hover:bg-green-700"}`}
          >
            {localLoading ? "Creando..." : "Crear Orden"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}