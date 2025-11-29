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
import { API_BASE_URL } from "@/lib/env";

/* ----------------------------- Tipos ----------------------------- */
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

// URLs de Supabase
const clientesUrl = `${API_BASE_URL}/clients/`;
const productosUrl = `${API_BASE_URL}/products/`;


/* ----------------------------- Props ----------------------------- */
interface EditOrderDialogProps {
  order: Orden;
  open: boolean;
  onClose: () => void;
  onSave: (edited: Orden) => void | Promise<void>; // ✅ acepta ambas
}


async function fetchJson(url: string, method: string = "GET", payload?: any) {
  const res = await fetch(url, {
    method,
    body: payload ? JSON.stringify(payload) : undefined
  });
  if (!res.ok) throw new Error(`${url} -> HTTP ${res.status}`);
  return res.json();
}

/* -------------------------- Componente -------------------------- */
export function EditOrderDialog({ order, open, onClose, onSave }: EditOrderDialogProps) {
  const [form, setForm] = useState<Orden>(() => {
    // Inicializar con la orden pero asegurando que tenga la estructura correcta
    const initialForm = structuredClone(order);
    
    // Asegurar que cliente tenga cliente_id (aunque sea vacío inicialmente)
    if (initialForm.cliente && !initialForm.cliente.cliente_id) {
      initialForm.cliente.cliente_id = "";
    }
    
    // Asegurar que cada item tenga producto_id
    initialForm.items = initialForm.items.map(item => ({
      ...item,
      producto_id: item.producto_id || ""
    }));
    
    return initialForm;
  });
  
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Cuando se cargan los clientes, buscar el ID del cliente actual por nombre
  useEffect(() => {
    if (clientes.length > 0 && form.cliente.nombre && !form.cliente.cliente_id) {
      const clienteEncontrado = clientes.find(c => c.nombre === form.cliente.nombre);
      if (clienteEncontrado) {
        console.log('✅ Cliente encontrado por nombre:', clienteEncontrado);
        setForm(prev => ({
          ...prev,
          cliente: {
            ...prev.cliente,
            cliente_id: clienteEncontrado.cliente_id
          }
        }));
      }
    }
  }, [clientes, form.cliente.nombre]);

  // Cuando se cargan los productos, buscar los IDs de productos actuales por nombre
  useEffect(() => {
    if (productos.length > 0 && form.items.length > 0) {
      const itemsActualizados = form.items.map(item => {
        // Si el item tiene nombre de producto pero no ID, buscar el ID
        if (item.producto?.nombre && !item.producto_id) {
          const productoEncontrado = productos.find(p => p.nombre === item.producto?.nombre);
          if (productoEncontrado) {
            console.log('✅ Producto encontrado por nombre:', productoEncontrado);
            return {
              ...item,
              producto_id: productoEncontrado.producto_id,
              producto: {
                nombre: productoEncontrado.nombre,
                producto_id: productoEncontrado.producto_id
              }
            };
          }
        }
        return item;
      });

      // Solo actualizar si hubo cambios
      const hayCambios = itemsActualizados.some((item, index) => 
        item.producto_id !== form.items[index].producto_id
      );

      if (hayCambios) {
        setForm(prev => ({
          ...prev,
          items: itemsActualizados
        }));
      }
    }
  }, [productos, form.items]);

  useEffect(() => {
    if (order) {
      console.log('🔄 Actualizando form con order:', order);
      const updatedForm = structuredClone(order);
      
      // Asegurar estructura correcta del cliente
      if (updatedForm.cliente && !updatedForm.cliente.cliente_id) {
        updatedForm.cliente.cliente_id = "";
      }
      
      // Asegurar que cada item tenga producto_id
      updatedForm.items = updatedForm.items.map(item => ({
        ...item,
        producto_id: item.producto_id || (item.producto?.producto_id || "") // MEJORA: Usar producto_id del producto si existe
      }));
      
      setForm(updatedForm);
    }
  }, [order]);
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Cargar clientes
        const clientesData = await fetchJson(clientesUrl);
        console.log('👥 Clientes cargados:', clientesData);
        setClientes(Array.isArray(clientesData) ? clientesData : []);

        // Cargar productos
        const productosData = await fetchJson(productosUrl);
        setProductos(Array.isArray(productosData) ? productosData : []);
      } catch (err) {
        console.error("Error cargando datos:", err);
      }
    };

    if (open) {
      fetchData();
    }
  }, [open]);

  // Añadir y eliminar items
  const addItem = () => {
    setForm((prev: Orden) => {
      const items = Array.isArray(prev.items) ? [...prev.items] : [];
      items.push({ 
        producto_id: "", 
        cantidad: 1, 
        precio_unitario: 0 
      });
      return { ...prev, items };
    });
  };

  const removeItem = (index: number) => {
    setForm((prev: Orden) => {
      const items = Array.isArray(prev.items) ? [...prev.items] : [];
      if (index >= 0 && index < items.length) items.splice(index, 1);
      return { ...prev, items };
    });
  };

  const handleChange = (path: string, value: any) => {
    const parts = path.split(".");
    
    // Manejar cambios en items
    if (parts[0] === "items" && parts.length >= 2) {
      const idx = Number(parts[1]);
      const prop = parts[2];
      const items = Array.isArray(form?.items) ? [...form.items] : [];
      const item = items[idx] ? { ...items[idx] } : { producto_id: "", cantidad: 0, precio_unitario: 0 };
      
      if (prop) {
        (item as any)[prop] = value;
        
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
      }
      
      items[idx] = item;
      setForm((prev) => ({ ...(prev as Orden), items } as Orden));
      return;
    }

    // Manejar cambios en cliente
    if (parts[0] === "cliente" && parts.length === 2) {
      const prop = parts[1];
      const newForm: any = { ...form };
      newForm.cliente = { ...newForm.cliente, [prop]: value };
      
      // Si cambiamos cliente_id, actualizar también el nombre del cliente
      if (prop === "cliente_id") {
        const cliente = clientes.find(c => c.cliente_id === value);
        if (cliente) {
          newForm.cliente.nombre = cliente.nombre;
        }
      }
      
      setForm(newForm as Orden);
      return;
    }

    // Generic shallow set for other top-level fields
    const newForm: any = { ...(form as any) };
    let current: any = newForm;
    for (let i = 0; i < parts.length - 1; i++) {
      const key = parts[i];
      if (current[key] == null) current[key] = {};
      current = current[key];
    }
    current[parts[parts.length - 1]] = value;
    setForm(newForm as Orden);
  };

  // Calcular total automáticamente cuando cambian los items
  useEffect(() => {
    try {
      const items = Array.isArray(form?.items) ? form.items : [];
      const total = items.reduce((acc, it) => {
        const qty = Number(it?.cantidad) || 0;
        const pu = Number(it?.precio_unitario) || 0;
        return acc + qty * pu;
      }, 0);
      if (form && form.total !== total) {
        setForm((prev) => ({ ...(prev as Orden), total } as Orden));
      }
    } catch (e) {
      // ignore
    }
  }, [form?.items]);

  const handleSave = async () => {
    if (!validate()) return;
    await onSave(form);
    onClose();
  };

  const validate = (): boolean => {
    if (!form) return false;
    
    const newErrors: Record<string, string> = {};
    if (!form?.cliente?.cliente_id) {
      newErrors["cliente_id"] = "Cliente requerido";
    }
    const items = Array.isArray(form?.items) ? form.items : [];
    if (items.length === 0) {
      newErrors["items"] = "Agregar al menos un item";
    }
    items.forEach((it, i) => {
      if (!it.producto_id) newErrors[`items.${i}.producto_id`] = "Producto requerido";
      if (!(Number(it.cantidad) > 0)) newErrors[`items.${i}.cantidad`] = "Cantidad debe ser mayor que 0";
      if (!(Number(it.precio_unitario) >= 0)) newErrors[`items.${i}.precio_unitario`] = "Precio debe ser >= 0";
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isFormValid = useMemo(() => {
    if (!form) return false;
    if (!form.cliente?.cliente_id) return false;
    const items = Array.isArray(form.items) ? form.items : [];
    if (items.length === 0) return false;
    
    for (const it of items) {
      if (!it.producto_id) return false;
      if (!(Number(it.cantidad) > 0)) return false;
      if (!(Number(it.precio_unitario) >= 0)) return false;
    }
    
    return true;
  }, [form]);

  const computedTotal = useMemo(() => {
    if (!form) return 0;
    return form.items.reduce((acc, item) => {
      return acc + (item.cantidad * item.precio_unitario);
    }, 0);
  }, [form?.items]);

  // Keep form.total in sync with computedTotal immediately
  useEffect(() => {
    if (!form) return;
    if (form.total !== computedTotal) {
      setForm(prev => prev ? { ...prev, total: computedTotal } : prev);
    }
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
                {/* Cliente - Muestra el cliente actual */}
                <div>
                  <Label className="mb-1.5">Cliente</Label>
                  <Select
                    value={form.cliente?.cliente_id || ""}
                    onValueChange={(value) => handleChange("cliente.cliente_id", value)}
                  >
                    <SelectTrigger>
                      <SelectValue>
                        {form.cliente?.nombre || "Seleccionar cliente"}
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
                      <SelectValue>{form.canal || "Seleccionar canal"}</SelectValue>
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
                    onValueChange={(value) => handleChange("moneda", value)}
                  >
                    <SelectTrigger>
                      <SelectValue>{form.moneda || "Seleccionar moneda"}</SelectValue>
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

          {/* --- Items --- */}
          {Array.isArray(form.items) && form.items.length > 0 && (
            <Card className="mb-2 border border-neutral-200 dark:border-neutral-800">
              <CardHeader className="flex items-center justify-between">
                <CardTitle className="text-neutral-700 dark:text-neutral-300">Items</CardTitle>
                <Button variant="outline" size="sm" onClick={addItem} className="ml-2">
                  Agregar item
                </Button>
              </CardHeader>

              <CardContent>
                <div className="mx-auto max-w-2xl space-y-6">
                  {form.items.map((item, i) => (
                    <div key={i} className="grid sm:grid-cols-4 gap-4 border-t pt-4 items-start">
                      {/* Producto - Muestra el producto actual */}
                      <div className="sm:col-span-2 min-w-0">
                        <Label className="mb-1">Producto</Label>
                        <Select
                          value={item.producto_id}
                          onValueChange={(value) => handleChange(`items.${i}.producto_id`, value)}
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
                        <Label className="mb-1">Cantidad</Label>
                        <Input
                          type="number"
                          value={item.cantidad}
                          onChange={(e) =>
                            handleChange(`items.${i}.cantidad`, Number(e.target.value))
                          }
                          className="w-full"
                        />
                        {errors[`items.${i}.cantidad`] && (
                          <p className="text-sm text-red-600 mt-1">{errors[`items.${i}.cantidad`]}</p>
                        )}
                      </div>

                      {/* Precio unitario */}
                      <div className="min-w-0">
                        <Label className="mb-1">Precio Unit</Label>
                        <Input
                          type="number"
                          value={item.precio_unitario}
                          onChange={(e) =>
                            handleChange(`items.${i}.precio_unitario`, Number(e.target.value))
                          }
                          className="w-full"
                        />
                        {errors[`items.${i}.precio_unitario`] && (
                          <p className="text-sm text-red-600 mt-1">{errors[`items.${i}.precio_unitario`]}</p>
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
          <div className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            {form?.moneda ?? ""} {computedTotal.toFixed(2)}
          </div>
        </div>

        <DialogFooter className="flex justify-end gap-3 mt-4">
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button 
            onClick={handleSave} 
            disabled={!isFormValid}
            className={`text-white ${!isFormValid ? "opacity-50 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"}`}
          >
            Guardar cambios
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}