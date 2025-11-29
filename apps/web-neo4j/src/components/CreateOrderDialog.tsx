import { useState, useEffect, useMemo } from "react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { API_BASE_URL } from "@/lib/env";

// --- Tipos base ---
export type Producto = {
  id: string;
  nombre: string;
  categoria: string;
  sku?: string;
  codigo_alt?: string;
  codigo_mongo?: string;
};

export type Cliente = {
  id: string;
  nombre: string;
  genero: "M" | "F" | "Otro" | "Masculino" | "Femenino";
  pais: string;
};

export type Contiene = {
  cantidad: number;
  precio_unit: number;
  producto: Producto;
};

export type Orden = {
  id?: string;
  fecha: string;
  canal: "WEB" | "TIENDA";
  moneda: "CRC" | "USD";
  total: number;
  cliente: Cliente;
  items: Contiene[];
  metadatos?: { cupon?: string } | null;
};

// --- Configuración ---
const clientesUrl = `${API_BASE_URL}/clients`;
const productosUrl = `${API_BASE_URL}/products`;

interface CreateOrderDialogProps {
  open: boolean;
  onClose: () => void;
  onCreate: (newOrder: any) => Promise<void>;
}

async function fetchJson(url: string) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export function CreateOrderDialog({ open, onClose, onCreate }: CreateOrderDialogProps) {
  const [form, setForm] = useState<Orden>({
    cliente: { id: "", nombre: "", genero: "Otro", pais: "" },
    fecha: new Date().toISOString(),
    canal: "WEB",
    moneda: "USD",
    total: 0,
    items: []
  });

  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [localLoading, setLocalLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [clientesData, productosData] = await Promise.all([
          fetchJson(clientesUrl),
          fetchJson(productosUrl)
        ]);

        setClientes(Array.isArray(clientesData) ? clientesData : clientesData?.data || []);
        setProductos(Array.isArray(productosData) ? productosData : productosData?.data || []);
      } catch (err) {
        console.error("Error cargando datos:", err);
      }
    };

    if (open) {
      fetchData();
      setForm({
        cliente: { id: "", nombre: "", genero: "Otro", pais: "" },
        fecha: new Date().toISOString(),
        canal: "WEB",
        moneda: "USD",
        total: 0,
        items: []
      });
      setErrors({});
    }
  }, [open]);

  const handleChange = (path: string, value: any) => {
    const parts = path.split(".");

    if (parts[0] === "cliente" && parts.length === 2) {
      if (parts[1] === "id") {
        const found = clientes.find(c => c.id === value);
        if (found) {
          setForm(prev => ({ 
            ...prev, 
            cliente: { ...found }
          }));
        } else {
          setForm(prev => ({ 
            ...prev, 
            cliente: { ...prev.cliente, id: value, nombre: "" } 
          }));
        }
      } else {
        setForm(prev => ({ 
          ...prev, 
          cliente: { ...prev.cliente, [parts[1]]: value } 
        }));
      }
      return;
    }

    if (parts[0] === "items" && parts.length >= 3) {
      const idx = Number(parts[1]);
      const prop = parts[2];
      const items = [...form.items];
      
      if (idx >= items.length) return;

      const item = { ...items[idx] };

      if (prop === "producto") {
        const found = productos.find(p => p.id === value);
        if (found) {
          item.producto = found;
        }
      } else {
        (item as any)[prop] = value;
      }

      items[idx] = item;
      setForm(prev => ({ ...prev, items }));
      return;
    }

    setForm(prev => ({ ...prev, [path]: value }));
  };

  const addItem = () => {
    setForm(prev => ({
      ...prev,
      items: [...prev.items, { 
        producto: { id: "", nombre: "", categoria: "" }, 
        cantidad: 1, 
        precio_unit: 0 
      }]
    }));
  };

  const removeItem = (index: number) => {
    setForm(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  const computedTotal = useMemo(() => {
    return form.items.reduce(
      (acc, it) => acc + (Number(it.cantidad) || 0) * (Number(it.precio_unit) || 0),
      0
    );
  }, [form.items]);

  // ✅ Validación completa de todos los campos requeridos
  const isFormValid = useMemo(() => {
    // Validar cliente
    if (!form.cliente.id) return false;
    
    // Validar fecha
    if (!form.fecha) return false;
    
    // Validar canal
    if (!form.canal) return false;
    
    // Validar moneda
    if (!form.moneda) return false;
    
    // Validar items
    if (form.items.length === 0) return false;
    
    // Validar cada item individualmente
    for (const item of form.items) {
      if (!item.producto.id) return false;
      if (!item.cantidad || item.cantidad <= 0) return false;
      if (item.precio_unit === undefined || item.precio_unit < 0) return false;
    }
    
    return true;
  }, [form]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!form.cliente.id) newErrors["cliente.id"] = "Cliente requerido";
    if (!form.fecha) newErrors["fecha"] = "Fecha requerida";
    if (!form.canal) newErrors["canal"] = "Canal requerido";
    if (!form.moneda) newErrors["moneda"] = "Moneda requerida";
    if (form.items.length === 0) newErrors["items"] = "Debe agregar al menos un item";

    form.items.forEach((it, i) => {
      if (!it.producto.id) newErrors[`items.${i}.producto`] = "Producto requerido";
      if (!it.cantidad || it.cantidad <= 0) newErrors[`items.${i}.cantidad`] = "Cantidad debe ser mayor a 0";
      if (it.precio_unit === undefined || it.precio_unit < 0) newErrors[`items.${i}.precio_unit`] = "Precio debe ser mayor o igual a 0";
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleCreate = async () => {
    if (!validate()) return;

    setLocalLoading(true);

    try {
      const orderToCreate = {
        cliente_id: form.cliente.id,
        fecha: form.fecha,
        canal: form.canal,
        moneda: form.moneda,
        total: computedTotal,
        items: form.items.map(item => ({
          producto_id: item.producto.id,
          cantidad: item.cantidad,
          precio_unit: item.precio_unit
        }))
      };

      await onCreate(orderToCreate);
      onClose();
    } catch (err) {
      console.error("Error creando orden:", err);
    } finally {
      setLocalLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Crear Nueva Orden</DialogTitle>
        </DialogHeader>

        <ScrollArea className="max-h-[70vh] pr-4">
          <Card className="mb-4">
            <CardHeader><CardTitle>Información General</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label className= "mb-2 ">Cliente</Label>
                <Select
                  value={form.cliente.id}
                  onValueChange={v => handleChange("cliente.id", v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar cliente" />
                  </SelectTrigger>
                  <SelectContent>
                    {clientes.map(c => (
                      <SelectItem key={c.id} value={c.id}>{c.nombre}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors["cliente.id"] && <p className="text-red-500 text-sm mt-1">{errors["cliente.id"]}</p>}
              </div>

              <div>
                <Label className= "mb-2 ">Fecha</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start">
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {form.fecha ? format(new Date(form.fecha), "dd/MM/yyyy") : "Seleccionar"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={new Date(form.fecha)}
                      onSelect={d => d && handleChange("fecha", d.toISOString())}
                    />
                  </PopoverContent>
                </Popover>
                {errors["fecha"] && <p className="text-red-500 text-sm mt-1">{errors["fecha"]}</p>}
              </div>

              <div>
                <Label className= "mb-2 ">Canal</Label>
                <Select
                  value={form.canal}
                  onValueChange={v => handleChange("canal", v)}
                >
                  <SelectTrigger >
                    <SelectValue  placeholder="Seleccionar canal" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem  value="WEB">WEB</SelectItem>
                    <SelectItem value="TIENDA">TIENDA</SelectItem>
                  </SelectContent>
                </Select>
                {errors["canal"] && <p className="text-red-500 text-sm mt-1">{errors["canal"]}</p>}
              </div>

              <div>
                <Label className= "mb-2 ">Moneda</Label>
                <Select
                  value={form.moneda}
                  onValueChange={v => handleChange("moneda", v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar moneda" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="CRC">CRC</SelectItem>
                  </SelectContent>
                </Select>
                {errors["moneda"] && <p className="text-red-500 text-sm mt-1">{errors["moneda"]}</p>}
              </div>
            </CardContent>
          </Card>

          <Card className="mb-4">
            <CardHeader className="flex justify-between items-center">
              <CardTitle>Items</CardTitle>
              <Button onClick={addItem} size="sm" variant="outline">Agregar</Button>
            </CardHeader>
            <CardContent>
              {errors["items"] && <p className="text-red-500 text-sm mb-3">{errors["items"]}</p>}
              
              {form.items.map((it, i) => (
                <div key={i} className="grid grid-cols-4 gap-3 border-t pt-3">
                  <div className="col-span-2">
                    <Label className= "mb-2 ">Producto</Label>
                    <Select
                      value={it.producto.id}
                      onValueChange={v => handleChange(`items.${i}.producto`, v)}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue className="truncate block" placeholder="Seleccionar producto" />
                      </SelectTrigger>
                      <SelectContent>
                        {productos.map(p => (
                          <SelectItem key={p.id} value={p.id}>{p.nombre}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors[`items.${i}.producto`] && <p className="text-red-500 text-sm mt-1">{errors[`items.${i}.producto`]}</p>}
                  </div>

                  <div>
                    <Label className= "mb-2 ">Cantidad</Label>
                    <Input
                      type="number"
                      min="1"
                      value={it.cantidad}
                      onChange={e => handleChange(`items.${i}.cantidad`, Number(e.target.value))}
                    />
                    {errors[`items.${i}.cantidad`] && <p className="text-red-500 text-sm mt-1">{errors[`items.${i}.cantidad`]}</p>}
                  </div>

                  <div>
                    <Label className= "mb-2 ">Precio Unit</Label>
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={it.precio_unit}
                      onChange={e => handleChange(`items.${i}.precio_unit`, Number(e.target.value))}
                    />
                    {errors[`items.${i}.precio_unit`] && <p className="text-red-500 text-sm mt-1">{errors[`items.${i}.precio_unit`]}</p>}
                  </div>
                </div>
              ))}

              {form.items.length === 0 && (
                <div className="text-center text-gray-500 py-4 border rounded">
                  No hay items agregados
                </div>
              )}
            </CardContent>
          </Card>
        </ScrollArea>

        <div className="px-6 pb-3 flex items-center justify-between">
          <span>Total:</span>
          <strong>{form.moneda} {computedTotal.toFixed(2)}</strong>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button 
            onClick={handleCreate} 
            disabled={localLoading || !isFormValid} 
          >
            {localLoading ? "Creando..." : "Crear Orden"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}