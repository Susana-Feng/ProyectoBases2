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
  precio_unit: number;
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

const apiBaseUrl = "https://dytnjcifruchjyrxguqe.supabase.co/rest/v1/";
const obtenerOrdenes = `${apiBaseUrl}orden_completa?select=*`;
const crearOrden = `${apiBaseUrl}rpc/fn_crear_orden`;
const actualizarOrdenCompleta = `${apiBaseUrl}rpc/fn_actualizar_orden_completa`;
const eliminarOrden = `${apiBaseUrl}rpc/fn_eliminar_orden`;

const supabaseHeaders = {
  "apikey": import.meta.env.VITE_SUPABASE_ANON_KEY,
  "Authorization": `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`,
  "Content-Type": "application/json"
};

export default function Orders() {
  const [orders, setOrders] = useState<Orden[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(10);
  const [hasMore, setHasMore] = useState(false);
  const [editingOrder, setEditingOrder] = useState<Orden | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  async function fetchJson(url: string, method: string = "GET", payload?: any) {
    const res = await fetch(url, {
      method,
      headers: supabaseHeaders,
      body: payload ? JSON.stringify(payload) : undefined
    });
    if (!res.ok) throw new Error(`${url} -> HTTP ${res.status}`);
    return res.json();
  }

  // --- Cargar órdenes ---
  async function loadOrders(offsetArg?: number, limitArg?: number) {
    setLoading(true);
    setError(null);
    try {
      const off = offsetArg ?? offset;
      const lim = limitArg ?? limit;

      // Calculate page index (0-based)
      const pageIndex = Math.floor(off / lim);

      const needDistinct = (pageIndex + 1) * lim + 1; // distinct orders required
      const batchSize = 200; // rows per request
      const maxRows = 5000; // safety cap

      let accumulated: any[] = [];
      let nextRowsOffset = 0;
      let finished = false;

      while (!finished && accumulated.length < maxRows) {
        const batch = await fetchJson(`${obtenerOrdenes}&offset=${nextRowsOffset}&limit=${batchSize}`);
        const rows = Array.isArray(batch) ? batch : [];
        if (rows.length === 0) {
          finished = true;
          break;
        }
        accumulated = accumulated.concat(rows);
        nextRowsOffset += rows.length;

        // quick check: count distinct orden_id in accumulated
        const distinct = new Set(accumulated.map(r => r.orden_id)).size;
        if (distinct >= needDistinct) finished = true;
        // if we've fetched a lot already, stop (maxRows cap)
        if (accumulated.length >= maxRows) finished = true;
      }

      // Group accumulated rows into orders in insertion order
      const ordersMap = new Map<string, any>();
      for (const item of accumulated) {
        if (!ordersMap.has(item.orden_id)) {
          ordersMap.set(item.orden_id, {
            orden_id: item.orden_id,
            fecha: item.fecha,
            canal: item.canal,
            moneda: item.moneda,
            total: item.total,
            cliente: { 
              cliente_id: item.cliente_id,
              nombre: item.nombre_cliente 
            },
            items: [],
            clienteLoading: false
          });
        }
        const order = ordersMap.get(item.orden_id);
        order.items.push({
          producto_id: item.producto_id,
          cantidad: item.cantidad,
          precio_unitario: item.precio_unitario,
          producto: { 
            producto_id: item.producto_id,
            nombre: item.nombre_producto 
          }
        });
      }

      const allOrders = Array.from(ordersMap.values());
      const start = pageIndex * lim;
      const list: Orden[] = allOrders.slice(start, start + lim);

      setOrders(list);
      setOffset(off);
      setLimit(lim);
      setHasMore(allOrders.length > start + lim);

    } catch (err: any) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  // --- Crear orden ---
  async function handleCreate(newOrder: Orden) {
    try {
      setLoading(true);
      setError(null);
      
      const body = {
        "p_cliente_id": newOrder.cliente.cliente_id,
        "p_fecha": newOrder.fecha,
        "p_canal": newOrder.canal,
        "p_moneda": newOrder.moneda,
        "p_items": newOrder.items.map(item => ({
          producto_id: item.producto_id,
          cantidad: item.cantidad,
          precio_unitario: item.precio_unitario
        }))
      };

      console.log('Creando nueva orden:', body);

      const res = await fetch(crearOrden, { 
        method: "POST", 
        headers: supabaseHeaders,
        body: JSON.stringify(body) 
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Error al crear orden: ${errorText}`);
      }
      
      await loadOrders(offset, limit);
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
      
      // Asegurar que la fecha esté en formato ISO string
      const fechaISO = new Date(edited.fecha).toISOString();
      
      const body = {
        "p_orden_id": edited.orden_id,
        "p_cliente_id": edited.cliente.cliente_id,
        "p_fecha": fechaISO,
        "p_canal": edited.canal,
        "p_moneda": edited.moneda,
        "p_items": edited.items.map(item => ({
          producto_id: item.producto_id,
          cantidad: item.cantidad,
          precio_unitario: item.precio_unitario
        }))
      };

      console.log('Enviando datos a fn_actualizar_orden_completa:', body);

      const res = await fetch(actualizarOrdenCompleta, { 
        method: "POST", 
        headers: supabaseHeaders,
        body: JSON.stringify(body) 
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        console.error('Error response:', errorText);
        throw new Error(`Error al actualizar orden: ${errorText}`);
      }
      
      const responseText = await res.text();
      if (responseText) {
        const result = JSON.parse(responseText);
        console.log('Orden actualizada exitosamente:', result);
      } else {
        console.log('Orden actualizada exitosamente (respuesta vacía)');
      }
      
      await loadOrders(offset, limit);
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
      
      const body = {
        "p_orden_id": o.orden_id
      };

      const res = await fetch(eliminarOrden, { 
        method: "POST", 
        headers: supabaseHeaders,
        body: JSON.stringify(body) 
      });
      
      if (!res.ok) throw new Error(await res.text());
      await loadOrders(offset, limit);
    } catch (err: any) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  const currentPage = limit > 0 ? Math.floor(offset / limit) + 1 : 1;

  useEffect(() => {
    loadOrders(0, limit);
  }, []);

  return (
    <div className="p-4 mx-auto bg-neutral-50 dark:bg-neutral-950 w-full h-screen overflow-hidden">
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

      <Table className="bg-neutral-100 dark:bg-neutral-900 rounded-sm">
        <TableCaption className="text-neutral-600 dark:text-neutral-400 text-center mx-auto">
          <div className="flex items-center justify-center gap-4">
            <div className="flex items-center gap-2">
              <Button 
                className="bg-neutral-900 dark:bg-neutral-600" 
                size="sm" 
                onClick={() => loadOrders(Math.max(0, offset - limit), limit)} 
                disabled={offset === 0 || loading}
              >
                <ArrowBigLeftDash className="dark:text-white"/>
              </Button>
              <Button 
                className="bg-neutral-900 dark:bg-neutral-600" 
                size="sm" 
                onClick={() => loadOrders(offset + limit, limit)} 
                disabled={!hasMore || loading}
              >
                <ArrowBigRightDash className="dark:text-white"/>
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm text-neutral-700 dark:text-neutral-300">Cantidad Órdenes</label>
              <select 
                value={limit} 
                onChange={(e) => { 
                  const l = Number(e.target.value) || 10; 
                  setLimit(l); 
                  setOffset(0); 
                  loadOrders(0, l); 
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
              {loading ? "Cargando..." : `Página ${currentPage}`}
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
                {new Date(o.fecha).toLocaleString()}
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