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
import type { Orden } from "@/pages/Orders";

/* ----------------------------- Tipos ----------------------------- */
interface Producto {
  id: string;
  nombre: string;
  categoria: string;
}

interface Cliente {
  id: string;
  nombre: string;
  genero: "M" | "F" | "Otro" | "Masculino" | "Femenino";
  pais: string;
}

// URLs
const apiBaseUrl = "http://localhost:8001/api/neo4j";
const clientesUrl = `${apiBaseUrl}/clients`;
const productosUrl = `${apiBaseUrl}/products`;

/* ----------------------------- Props ----------------------------- */
interface EditOrderDialogProps {
  order: Orden;
  open: boolean;
  onClose: () => void;
  onSave: (edited: any) => void | Promise<void>;
}

async function fetchJson(url: string) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/* -------------------------- Componente -------------------------- */
export function EditOrderDialog({ order, open, onClose, onSave }: EditOrderDialogProps) {
  // ✅ CORREGIDO: Usar la estructura correcta de tipos
  const [form, setForm] = useState<Orden>(() => structuredClone(order));
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [localLoading, setLocalLoading] = useState(false);

  // Actualizar form cuando cambia la orden
  useEffect(() => {
    if (order && open) {
      setForm(structuredClone(order));
    }
  }, [order, open]);

  // Cargar datos cuando se abre el dialog
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
      setErrors({});
    }
  }, [open]);

  // ✅ CORREGIDO: Añadir item con estructura Contiene correcta
  const addItem = () => {
    setForm(prev => {
      const items = Array.isArray(prev.items) ? [...prev.items] : [];
      items.push({ 
        cantidad: 1, 
        precio_unit: 0,
        producto: { id: "", nombre: "", categoria: "" }
      });
      return { ...prev, items };
    });
  };

  const removeItem = (index: number) => {
    setForm(prev => {
      const items = Array.isArray(prev.items) ? [...prev.items] : [];
      if (index >= 0 && index < items.length) items.splice(index, 1);
      return { ...prev, items };
    });
  };

  const handleChange = (path: string, value: any) => {
    const parts = path.split(".");
    
    // Manejar cambios en items
    if (parts[0] === "items" && parts.length >= 3) {
      const idx = Number(parts[1]);
      const prop = parts[2];
      
      setForm(prev => {
        const items = Array.isArray(prev.items) ? [...prev.items] : [];
        const item = items[idx] ? { ...items[idx] } : { 
          cantidad: 1,
          precio_unit: 0,
          producto: { id: "", nombre: "", categoria: "" }
        };
        
        if (prop === "producto" && parts[3] === "id") {
          const productoId = value;
          const productoEncontrado = productos.find(p => p.id === productoId);
          if (productoEncontrado) {
            item.producto = {
              id: productoEncontrado.id,
              nombre: productoEncontrado.nombre,
              categoria: productoEncontrado.categoria
            };
          } else {
            item.producto = { id: productoId, nombre: "", categoria: "" };
          }
        } else {
          (item as any)[prop] = value;
        }
        
        items[idx] = item;
        return { ...prev, items };
      });
      return;
    }

    // Campos simples
    setForm(prev => {
      const newForm = { ...prev };
      const partsGen = parts;
      let current: any = newForm;
      for (let i = 0; i < partsGen.length - 1; i++) {
        const key = partsGen[i];
        if (current[key] == null) current[key] = {};
        current = current[key];
      }
      current[partsGen[partsGen.length - 1]] = value;
      return newForm;
    });
  };

  // Calcular total
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

  // Sincronizar total del form
  useEffect(() => {
    if (!form) return;
    if (form.total !== computedTotal) {
      setForm(prev => ({ ...prev, total: computedTotal }));
    }
  }, [computedTotal]);

  // ✅ CORREGIDO: Validación usando la estructura correcta
  const isFormValid = useMemo(() => {
    if (!form) return false;
    if (!form.cliente?.id) return false;
    const items = Array.isArray(form.items) ? form.items : [];
    if (items.length === 0) return false;
    
    // Verificar que no haya productos duplicados
    const productosIds = items.map(it => it.producto?.id).filter(Boolean);
    const tieneDuplicados = new Set(productosIds).size !== productosIds.length;
    if (tieneDuplicados) return false;
    
    for (const it of items) {
      if (!it.producto?.id) return false;
      if (!(Number(it.cantidad) > 0)) return false;
      if (!(Number(it.precio_unit) >= 0)) return false;
    }
    
    return true;
  }, [form]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!form?.cliente?.id) newErrors["cliente"] = "Cliente requerido";
    const items = Array.isArray(form?.items) ? form.items : [];
    if (items.length === 0) newErrors["items"] = "Agregar al menos un item";

    // Verificar productos duplicados
    const productosIds = items.map(it => it.producto?.id).filter(Boolean);
    const productosDuplicados = productosIds.filter((id, index) => 
      productosIds.indexOf(id) !== index
    );
    if (productosDuplicados.length > 0) {
      newErrors["items"] = "No puede haber productos duplicados en la orden";
    }

    items.forEach((it, i) => {
      if (!it.producto?.id) newErrors[`items.${i}.producto`] = "Producto requerido";
      if (!(Number(it.cantidad) > 0)) newErrors[`items.${i}.cantidad`] = "Cantidad debe ser mayor que 0";
      if (!(Number(it.precio_unit) >= 0)) newErrors[`items.${i}.precio_unit`] = "Precio debe ser >= 0";
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // ✅ CORREGIDO: handleSave usando la estructura correcta para el backend
  const handleSave = async () => {
    if (!validate()) return;

    setLocalLoading(true);
    try {
      const orderToSave = {
        id: form.id,
        cliente_id: form.cliente.id,
        fecha: form.fecha,
        canal: form.canal,
        moneda: form.moneda,
        total: computedTotal,
        items: form.items.map(item => ({
          producto_id: item.producto.id, // ✅ Usar producto.id como producto_id
          cantidad: item.cantidad,
          precio_unit: item.precio_unit
        }))
      };

      await onSave(orderToSave);
      onClose();
    } catch (err) {
      console.error("Error guardando orden:", err);
    } finally {
      setLocalLoading(false);
    }
  };

  if (!form) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Editar Orden</DialogTitle>
        </DialogHeader>

        <ScrollArea className="max-h-[70vh] pr-4">
          {/* --- Información general --- */}
          <Card className="mb-4">
            <CardHeader>
              <CardTitle>Información general</CardTitle>
            </CardHeader>

            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label>Cliente</Label>
                <Select
                  value={form.cliente?.id || ""}
                  onValueChange={(value) => handleChange("cliente.id", value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar cliente" />
                  </SelectTrigger>
                  <SelectContent>
                    {clientes.map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors["cliente"] && (
                  <p className="text-sm text-red-600 mt-1">{errors["cliente"]}</p>
                )}
              </div>

              <div>
                <Label>Fecha</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start">
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {form.fecha ? format(new Date(form.fecha), "dd/MM/yyyy") : "Seleccionar fecha"}
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

              <div>
                <Label>Canal</Label>
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

              <div>
                <Label>Moneda</Label>
                <Select
                  value={form.moneda}
                  onValueChange={(value) => handleChange("moneda", value)}
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
            </CardContent>
          </Card>

          {/* --- Items --- */}
          <Card className="mb-4">
            <CardHeader className="flex justify-between items-center">
              <CardTitle>Items</CardTitle>
              <Button onClick={addItem} size="sm" variant="outline">
                Agregar Item
              </Button>
            </CardHeader>

            <CardContent>
              {errors["items"] && (
                <p className="text-red-500 text-sm mb-3">{errors["items"]}</p>
              )}
              
              {Array.isArray(form.items) && form.items.map((item, i) => (
                <div key={i} className="grid grid-cols-4 gap-3 border-t pt-3">
                  <div className="col-span-2">
                    <Label>Producto</Label>
                    <Select
                      value={item.producto?.id || ""}
                      onValueChange={(value) => handleChange(`items.${i}.producto.id`, value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccionar producto" />
                      </SelectTrigger>
                      <SelectContent>
                        {productos.map((p) => (
                          <SelectItem key={p.id} value={p.id}>
                            {p.nombre}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors[`items.${i}.producto`] && (
                      <p className="text-sm text-red-600 mt-1">{errors[`items.${i}.producto`]}</p>
                    )}
                  </div>

                  <div>
                    <Label>Cantidad</Label>
                    <Input
                      type="number"
                      min="1"
                      value={item.cantidad}
                      onChange={(e) =>
                        handleChange(`items.${i}.cantidad`, Number(e.target.value))
                      }
                    />
                    {errors[`items.${i}.cantidad`] && (
                      <p className="text-sm text-red-600 mt-1">{errors[`items.${i}.cantidad`]}</p>
                    )}
                  </div>

                  <div>
                    <Label>Precio Unit</Label>
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.precio_unit}
                      onChange={(e) =>
                        handleChange(`items.${i}.precio_unit`, Number(e.target.value))
                      }
                    />
                    {errors[`items.${i}.precio_unit`] && (
                      <p className="text-sm text-red-600 mt-1">{errors[`items.${i}.precio_unit`]}</p>
                    )}
                  </div>

                  <div className="flex items-end">
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

              {(!form.items || form.items.length === 0) && (
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
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button 
            onClick={handleSave} 
            disabled={localLoading || !isFormValid}
          >
            {localLoading ? "Guardando..." : "Guardar Cambios"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}