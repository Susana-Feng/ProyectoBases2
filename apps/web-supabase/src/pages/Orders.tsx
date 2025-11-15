import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableCaption } from "@/components/ui/table";
import DarkToggle from "@/components/DarkToggle";
import { ArrowBigLeftDash, ArrowBigRightDash } from 'lucide-react';
import { EditOrderDialog } from "@/components/EditOrderDialog";
import { CreateOrderDialog } from "@/components/CreateOrderDialog";

export type Item = {
  orden_detalle_id?: string;
  orden_id: string;
  producto_id: string;
  cantidad: number;
  precio_unitario: number;
};

export interface Orden {
  orden_id?: string;
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

const apiBaseUrl = "http://localhost:8002/api/supabase/";
const obtenerOrdenes = `${apiBaseUrl}orders/`;
const crearOrden = `${apiBaseUrl}orders/`;
const actualizarOrdenCompleta = `${apiBaseUrl}orders/`;
const eliminarOrden = `${apiBaseUrl}orders/`;

export default function Orders() {
  const [orders, setOrders] = useState<Orden[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [ordersPerPage, setOrdersPerPage] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [editingOrder, setEditingOrder] = useState<Orden | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [allOrders, setAllOrders] = useState<Orden[]>([]);

  async function fetchJson<T>(url: string, method: string = "GET", payload?: any): Promise<T> {
    const options: RequestInit = {
      method,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    };

    if (method !== 'GET' && payload) {
      options.body = JSON.stringify(payload);
    }

    console.log(`Fetching: ${url}`, options);

    const res = await fetch(url, options);

    console.log('Response status:', res.status);

    if (!res.ok) {
      const errorText = await res.text().catch(() => 'No error details');
      throw new Error(`${url} -> HTTP ${res.status}: ${errorText}`);
    }

    return res.json() as Promise<T>;
  }

  // Función para cargar todas las órdenes
  async function loadAllOrders() {
    setLoading(true);
    setError(null);
    try {
      console.log('📊 Cargando todas las órdenes...');

      // Cargar una cantidad grande de órdenes para determinar el total
      const response = await fetchJson(`${obtenerOrdenes}?offset=0&limit=1000`);
      const rows = Array.isArray(response) ? response : [];

      // Agrupar items por orden_id
      const ordersMap = new Map<string, any>();
      for (const item of rows) {
        if (!ordersMap.has(item.orden_id)) {
          ordersMap.set(item.orden_id, {
            orden_id: item.orden_id,
            fecha: item.fecha,
            canal: item.canal,
            moneda: item.moneda,
            total: item.total,
            cliente: {
              cliente_id: item.cliente_id,
              nombre: item.nombre_cliente,
            },
            items: [],
          });
        }
        const order = ordersMap.get(item.orden_id);
        order.items.push({
          producto_id: item.producto_id,
          cantidad: item.cantidad,
          precio_unitario: item.precio_unitario,
          producto: {
            producto_id: item.producto_id,
            nombre: item.nombre_producto,
          },
        });
      }

      const allOrdersArray = Array.from(ordersMap.values());
      console.log(`✅ ${allOrdersArray.length} órdenes totales encontradas`);

      setAllOrders(allOrdersArray);
      updatePagination(allOrdersArray, ordersPerPage, 1);

    } catch (err: any) {
      console.error('❌ Error loading all orders:', err);
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  // Función para actualizar la paginación basada en las órdenes y configuración actual
  function updatePagination(ordersArray: Orden[], perPage: number, page: number) {
    // Calcular el total de páginas
    const calculatedTotalPages = Math.ceil(ordersArray.length / perPage);
    setTotalPages(calculatedTotalPages);

    // Calcular el rango de órdenes para la página actual
    const startIndex = (page - 1) * perPage;
    const endIndex = startIndex + perPage;
    const currentPageOrders = ordersArray.slice(startIndex, endIndex);

    console.log(`📄 Página ${page} de ${calculatedTotalPages}, mostrando ${currentPageOrders.length} órdenes de ${ordersArray.length} totales`);

    setOrders(currentPageOrders);
    setCurrentPage(page);
  }

  // Función para cambiar de página
  function goToPage(page: number) {
    if (page < 1 || page > totalPages) return;
    updatePagination(allOrders, ordersPerPage, page);
  }

  // Función para cambiar el número de órdenes por página
  function handleOrdersPerPageChange(newLimit: number) {
    setOrdersPerPage(newLimit);
    // Reiniciar a la página 1 con el nuevo límite
    updatePagination(allOrders, newLimit, 1);
  }

  // --- Crear orden ---
  async function handleCreate(newOrder: Orden) {
    try {
      setLoading(true);
      setError(null);
      
      const total = newOrder.items.reduce((sum, item) => {
        return sum + (item.cantidad * item.precio_unitario);
      }, 0);

      const body = {
        "cliente_id": newOrder.cliente.cliente_id,
        "fecha": newOrder.fecha,
        "canal": newOrder.canal,
        "moneda": newOrder.moneda,
        "total": total,
        "items": newOrder.items.map(item => ({
          producto_id: item.producto_id,
          cantidad: item.cantidad,
          precio_unitario: item.precio_unitario
        }))
      };

      console.log('Creando nueva orden:', body);

      const res = await fetch(crearOrden, {
        method: "POST",
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Error al crear orden: ${errorText}`);
      }
      
      // Recargar todas las órdenes
      await loadAllOrders();
      
    } catch (err: any) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  // --- Editar orden ---
  async function handleSave(edited: Orden) {
    try {
      setLoading(true);
      setError(null);
      
      const total = edited.items.reduce((sum, item) => {
        return sum + (item.cantidad * item.precio_unitario);
      }, 0);

      const fechaISO = new Date(edited.fecha).toISOString();
      
      // 🔹 CORREGIDO: El orden_id va en la URL, no en el body
      const body = {
        "cliente_id": edited.cliente.cliente_id,
        "fecha": fechaISO,
        "canal": edited.canal,
        "moneda": edited.moneda,
        "total": total,
        "items": edited.items.map(item => ({
          producto_id: item.producto_id,
          cantidad: item.cantidad,
          precio_unitario: item.precio_unitario
        }))
      };

      // 🔹 CORREGIDO: Incluir el orden_id en la URL
      const url = `${actualizarOrdenCompleta}${edited.orden_id}`;
      console.log('Enviando datos para actualizar a URL:', url);
      console.log('Body:', body);

      const res = await fetch(url, { 
        method: "PUT", 
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(body) 
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        console.error('Error response:', errorText);
        throw new Error(`Error al actualizar orden: ${errorText}`);
      }
      
      // Actualizar en el estado local
      const updatedAllOrders = allOrders.map(order => 
        order.orden_id === edited.orden_id ? edited : order
      );
      setAllOrders(updatedAllOrders);
      
      // Actualizar la vista actual manteniendo la página y límite actual
      updatePagination(updatedAllOrders, ordersPerPage, currentPage);
      
    } catch (err: any) {
      console.error('Error completo:', err);
      setError(err.message || String(err));
    } finally {
      setLoading(false);
      setDialogOpen(false);
    }
  }

  // --- Eliminar orden ---
  async function deleteOrder(o: Orden) {
    if (!confirm("Eliminar orden?")) return;
    try {
      setLoading(true);
      setError(null);
      
      const url = `${eliminarOrden}${o.orden_id}`;
      console.log('Eliminando orden con URL:', url);

      const res = await fetch(url, { 
        method: "DELETE", // Usar DELETE method
        headers: {
          'Accept': 'application/json',
        },
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Error al eliminar orden: ${errorText}`);
      }
      
      // Recargar todas las órdenes
      await loadAllOrders();
    } catch (err: any) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  const hasNextPage = currentPage < totalPages;
  const hasPrevPage = currentPage > 1;

  useEffect(() => {
    loadAllOrders();
  }, []);

    return (
    <div className="p-4 mx-auto bg-neutral-50 dark:bg-neutral-950 w-full min-h-screen"> {/* Cambiado a min-h-screen */}
      <div className="flex items-center justify-center mb-4">
        <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 text-center">Órdenes</h2>
        <div className="absolute right-0 mr-9"><DarkToggle /></div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div>
        <Button variant="outline" onClick={() => setCreateDialogOpen(true)} disabled={loading} className="mb-4 bg-neutral-400 dark:bg-neutral-800 text-white">
          Crear Nueva Orden
        </Button>
      </div>

      {/* Tabla sin contenedor de scroll - se expandirá naturalmente */}
      <Table className="bg-neutral-100 dark:bg-neutral-900 rounded-sm w-full">
        <TableCaption className="text-neutral-600 dark:text-neutral-400 text-center mx-auto">
          <div className="flex items-center justify-center gap-4">
            <div className="flex items-center gap-2">
              <Button
                className="bg-neutral-900 dark:bg-neutral-600"
                size="sm"
                onClick={() => goToPage(currentPage - 1)}
                disabled={!hasPrevPage || loading}
              >
                <ArrowBigLeftDash className="dark:text-white" />
              </Button>

              <Button
                className="bg-neutral-900 dark:bg-neutral-600"
                size="sm"
                onClick={() => goToPage(currentPage + 1)}
                disabled={!hasNextPage || loading}
              >
                <ArrowBigRightDash className="dark:text-white" />
              </Button>

            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm text-neutral-700 dark:text-neutral-300">Órdenes por página</label>
              <select 
                value={ordersPerPage} 
                onChange={(e) => { 
                  const newLimit = Number(e.target.value) || 10; 
                  handleOrdersPerPageChange(newLimit);
                }} 
                className="text-sm p-1 border rounded bg-white dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100"
                disabled={loading}
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
            </div>
            <div className="text-sm text-neutral-700 dark:text-neutral-300 ml-3">
              {loading ? "Cargando..." : `Página ${currentPage} de ${totalPages}`}
            </div>
          </div>
        </TableCaption>

        <TableHeader>
          <TableRow className="bg-neutral-200 dark:bg-neutral-800">
            <TableHead className="text-center text-neutral-900 dark:text-neutral-100 rounded-tl-sm">Cliente</TableHead>
            <TableHead className="text-center text-neutral-900 dark:text-neutral-100">Fecha</TableHead>
            <TableHead className="text-center text-neutral-900 dark:text-neutral-100">Canal</TableHead>
            <TableHead className="text-center text-neutral-900 dark:text-neutral-100">Moneda</TableHead>
            <TableHead className="text-center text-neutral-900 dark:text-neutral-100">Total</TableHead>
            <TableHead className="text-center text-neutral-900 dark:text-neutral-100">Items</TableHead>
            <TableHead className="text-center text-neutral-900 dark:text-neutral-100 rounded-tr-sm">Acciones</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {loading && (
            <TableRow>
              <TableCell colSpan={7} className="p-4 text-center text-neutral-500 dark:text-neutral-400">
                Cargando órdenes...
              </TableCell>
            </TableRow>
          )}

          {!loading && orders.length === 0 && (
            <TableRow>
              <TableCell colSpan={7} className="p-4 text-center text-neutral-500 dark:text-neutral-400">
                No hay órdenes
              </TableCell>
            </TableRow>
          )}

          {!loading && orders.map(o => (
            <TableRow key={o.orden_id} className="border-neutral-200 dark:border-neutral-800">
              <TableCell className="text-center">
                {o.cliente?.nombre ?? "Desconocido"}
              </TableCell>
              <TableCell className="text-center">
                {new Date(o.fecha).toLocaleDateString()}
              </TableCell>
              <TableCell className="text-center">
                {o.canal}
              </TableCell>
              <TableCell className="text-center">
                {o.moneda}
              </TableCell>
              <TableCell className="text-center">
                {typeof o.total === 'number' ? o.total.toLocaleString() : o.total}
              </TableCell>
              <TableCell className="text-center">
                {(o.items || []).map((it, i) => (
                  <div key={i} className="text-sm">
                    {it.producto?.nombre ?? "Producto"} — {it.cantidad} × {it.precio_unitario?.toLocaleString()}
                  </div>
                ))}
              </TableCell>
              <TableCell className="text-center">
                <Button 
                  variant="secondary" 
                  size="sm" 
                  onClick={() => { setEditingOrder(o); setDialogOpen(true); }} 
                  className="mr-2"
                  disabled={loading}
                >
                  Editar
                </Button>
                <Button 
                  variant="destructive" 
                  size="sm" 
                  onClick={() => deleteOrder(o)}
                  disabled={loading}
                >
                  Eliminar
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {editingOrder && (
        <EditOrderDialog
          order={editingOrder}
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          onSave={handleSave}
        />
      )}
      
      {createDialogOpen && (
        <CreateOrderDialog 
          open={createDialogOpen} 
          onClose={() => setCreateDialogOpen(false)} 
          onCreate={handleCreate}
        />
      )}
    </div>
  );
}