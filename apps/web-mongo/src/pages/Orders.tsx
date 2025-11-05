import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableCaption } from "@/components/ui/table";
import DarkToggle from "@/components/DarkToggle";
import { ArrowBigLeftDash, ArrowBigRightDash } from 'lucide-react';
import { EditOrderDialog } from "@/components/EditOrderDialog";
import { CreateOrderDialog } from "@/components/CreateOrderDialog";

type Item = {
  producto_id: string;
  cantidad: number;
  precio_unit: number;
};

type Orden = {
  _id?: string;
  cliente_id: string;
  fecha: string; // ISO
  canal: "WEB" | "TIENDA";
  moneda: "CRC" | "USD";
  total: number;
  items: Item[];
  metadatos?: { cupon?: string } | null;
};

const apiBaseUrl = "http://localhost:8000/api/mongo";
const rutaBase = apiBaseUrl + "/order";
const rutaCliente = apiBaseUrl + "/clients";
const rutaProducto = apiBaseUrl + "/products";

export default function Orders() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [skip, setSkip] = useState<number>(0);
  const [limit, setLimit] = useState<number>(10);
  const [total, setTotal] = useState<number | null>(null);
  const [editingOrder, setEditingOrder] = useState<any | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [hasMore, setHasMore] = useState<boolean>(false);

  // Pagination helpers
  // Compute pagination display. If backend `total` exists but is smaller than
  // the number of items we currently have (could be inconsistent), use at
  // least `skip + orders.length` so the page count doesn't shrink unexpectedly.
  const currentPage = limit > 0 ? Math.floor(skip / limit) + 1 : 1;
  const knownTotal = typeof total === "number" ? Math.max(total, skip + orders.length) : undefined;
  const totalPages = typeof knownTotal === "number" && limit > 0 ? Math.max(1, Math.ceil(knownTotal / limit)) : undefined;

  // Cachés para no repetir peticiones
  const clienteCache = new Map<string, any>();
  const productoCache = new Map<string, any>();

  async function fetchJson(url: string) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${url} -> HTTP ${res.status}`);
    const contentType = res.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      const text = await res.text();
      throw new Error(
        `Expected JSON from ${url} but got ${contentType || "<no content-type>"}: ${text.slice(
          0,
          200
        )}`
      );
    }
    return res.json();
  }

  // Obtener cliente por ID
  async function getCliente(id: string) {
    if (!id) return null;
    // normalize id: trim and strip surrounding quotes
    const cleanId = String(id).trim().replace(/^["']+|["']+$/g, "");
    if (clienteCache.has(cleanId)) return clienteCache.get(cleanId);

    try {
      const data = await fetchJson(`${rutaCliente}/${cleanId}`);
      const payload = data?.data ?? data;
      let cliente = null as any;
      if (Array.isArray(payload)) {
        cliente = payload.find((c: any) => String(c._id) === cleanId || String(c.id) === cleanId) ?? payload[0] ?? null;
      } else if (payload && typeof payload === "object") {
        cliente = payload;
      }
      clienteCache.set(cleanId, cliente);
      return cliente;
    } catch (err) {
      try {
        const listData = await fetchJson(`${rutaCliente}/?limit=200`);
        const arr = listData?.data ?? listData;
        if (Array.isArray(arr)) {
          const found = arr.find((c: any) => String(c._id) === cleanId || String(c.id) === cleanId) ?? null;
          clienteCache.set(cleanId, found);
          return found;
        }
      } catch (e) {
        // ignore
      }
      clienteCache.set(cleanId, null);
      return null;
    }
  }

  // Obtener producto por ID
  async function fetchProducto(id: string) {
    if (!id) return null;
    if (productoCache.has(id)) return productoCache.get(id);
    try {
      const data = await fetchJson(`${rutaProducto}/${id}`);
      const producto = data?.data ?? data;
      productoCache.set(id, producto);
      return producto;
    } catch (err) {
      productoCache.set(id, null);
      return null;
    }
  }

  // Eliminar productos por ID
  async function deleteProducto(o: any) {
    try {
      const res = await fetch(`${rutaBase}/${o._id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await loadOrders(skip, limit);
      } catch (err: any) {
      setError(err.message || String(err));
    }
  }

  async function editOrder(o: any) {
    setEditingOrder(o);
    setDialogOpen(true);
  }

  async function handleSave(edited: any) {
    try {
      setLoading(true);
      setError(null);

      const res = await fetch(`${rutaBase}/${edited._id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(edited),
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `HTTP ${res.status}`);
      }

      await loadOrders(skip, limit);
    } catch (err: any) {
      setError(err?.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  // Crear nueva orden
  async function handleCreate(newOrder: any) {
    try {
      setLoading(true);
      setError(null);

      const res = await fetch(rutaBase, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newOrder),
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `HTTP ${res.status}`);
      }

      await loadOrders(skip, limit);
    } catch (err: any) {
      setError(err?.message || String(err));
    } finally {
      setLoading(false);
      setCreateDialogOpen(false);
    }
  }


  // Cargar todas las órdenes
  async function loadOrders(skipArg?: number, limitArg?: number) {
    setLoading(true);
    setError(null);
    try {
      const s = typeof skipArg === "number" ? skipArg : skip;
      const l = typeof limitArg === "number" ? limitArg : limit;
      // fetch one extra item to detect if there is a next page when backend
      // does not return a reliable total
      const url = `${rutaBase}/?skip=${s}&limit=${l + 1}`;
      const data = await fetchJson(url);
      const rawList = data?.data ?? data ?? [];
      const list = Array.isArray(rawList) ? rawList.slice(0, l) : [];
      const extraCount = Array.isArray(rawList) ? rawList.length : 0;
      setHasMore(extraCount > l);

  if (typeof data?.total === "number") setTotal(data.total);
  if (typeof data?.skip === "number") setSkip(data.skip);
  else setSkip(s);
  // Always keep the UI page size as the requested `l` (we requested l+1 to detect hasMore)
  setLimit(l);

  const initial = list.map((o: any) => ({ ...o, cliente: null, clienteLoading: true }));
      setOrders(initial);

      list.forEach((o: any) => {
        (async () => {
          const cliente = await getCliente(o.cliente_id);

          const items = await Promise.all(
            (o.items || []).map(async (it: any) => {
              const producto = await fetchProducto(it.producto_id);
              return { ...it, producto: producto ?? null };
            })
          );

          setOrders((prev) =>
            prev.map((p: any) => (p._id === o._id ? { ...p, cliente, clienteLoading: false, items } : p))
          );
        })();
      });
    } catch (err: any) {
      setError(err?.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOrders(0, limit);
  }, []);
return (

  <div className="p-4  mx-auto bg-neutral-50 dark:bg-neutral-950 w-full h-screen overflow-hidden ">
      <div className="flex items-center  justify-center mb-4">
        <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 text-center">
          Órdenes
        </h2>

        <div className="absolute right-0 mr-9">
          <DarkToggle />
        </div>
        </div>
        <div>
          <Button variant="outline" onClick={() => setCreateDialogOpen(true)} disabled={loading} className="mb-4 bg-neutral-400 dark:bg-neutral-800 text-white">
            Crear Nueva Orden
          </Button>
        </div>
      <Table className="bg-neutral-100 dark:bg-neutral-900 rounded-sm ">
        <TableCaption className="text-neutral-600 dark:text-neutral-400 text-center mx-auto">
  <div className="flex items-center justify-center gap-4">
            <div className="flex items-center gap-2">
            <Button className="bg-neutral-900 dark:bg-neutral-600" size="sm" onClick={() => loadOrders(Math.max(0, skip - limit), limit)} disabled={skip === 0}>
                <ArrowBigLeftDash className="dark:text-white"/>
            </Button>
            {/* Next button: enable when total indicates more pages, or when hasMore is true (we fetched limit+1) */}
            <Button
              className="bg-neutral-900 dark:bg-neutral-600"
              size="sm"
              onClick={() => loadOrders(skip + limit, limit)}
              disabled={
                loading || (typeof total === "number" ? skip + limit >= total : !hasMore)
              }
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
                setSkip(0);
                loadOrders(0, l);
                }}
                className="text-sm p-1 border rounded bg-white dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100"
            >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
            </select>
            </div>
      <div className="text-sm text-neutral-700 dark:text-neutral-300">
      {orders.length > 0 ? (
        <>
        {typeof totalPages === "number" && (
          <span className="ml-3"> Página {currentPage} de {totalPages}</span>
        )}
        </>
      ) : (
        <>No hay resultados</>
      )}
      </div>
        </div>
        </TableCaption>
        <TableHeader >
          <TableRow className="bg-neutral-200 dark:bg-neutral-800  ">
            <TableHead className="text-center text-neutral-900 dark:text-neutral-100 rounded-tl-sm">
              Cliente
            </TableHead>
            <TableHead className="text-center text-neutral-900 dark:text-neutral-100">
              Fecha
            </TableHead>
            <TableHead className="text-center text-neutral-900 dark:text-neutral-100">
              Canal
            </TableHead>
            <TableHead className="text-center text-neutral-900 dark:text-neutral-100">
              Moneda
            </TableHead>
            <TableHead className=" text-center text-neutral-900 dark:text-neutral-100">
              Total
            </TableHead>
            <TableHead className="text-neutral-900 text-center dark:text-neutral-100">
              Items
            </TableHead>
            <TableHead className="text-neutral-900 text-center dark:text-neutral-100 rounded-tr-sm">
              Acciones
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody className="p-1.5 text-center">
          {orders.length === 0 && !loading && (
            <TableRow>
              <TableCell 
                className="p-4 text-center text-neutral-500 dark:text-neutral-400" 
                colSpan={7}
              >
                No hay órdenes
              </TableCell>
            </TableRow>
          )}

          {orders.map((o: any) => (
            <TableRow 
              key={o._id}
              className="border-neutral-200 dark:border-neutral-800"
            >
              <TableCell className="text-neutral-900 dark:text-neutral-100">
                {o.clienteLoading ? (
                  <span className="text-neutral-500 dark:text-neutral-400">
                    Cargando...
                  </span>
                ) : o.cliente && o.cliente.nombre ? (
                  o.cliente.nombre
                ) : o.cliente === null ? (
                  <span className="text-neutral-400 dark:text-neutral-500">
                    Desconocido
                  </span>
                ) : (
                  o.cliente_id
                )}
              </TableCell>
              <TableCell className="text-neutral-700 dark:text-neutral-300">
                {new Date(o.fecha).toLocaleString()}
              </TableCell>
              <TableCell className="text-neutral-700 dark:text-neutral-300">
                {o.canal}
              </TableCell>
              <TableCell className="text-neutral-700 dark:text-neutral-300">
                {o.moneda}
              </TableCell>
              <TableCell className=" text-neutral-900 dark:text-neutral-100">
                {o.total}
              </TableCell>
              <TableCell className="text-neutral-700 dark:text-neutral-300">
                {(o.items || []).map((it: any, i: number) => (
                  <div key={i} className="text-sm">
                    {it.producto?.nombre ?? it.producto_id} — {it.cantidad} × {it.precio_unit}
                  </div>
                ))}
              </TableCell>
              <TableCell>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => editOrder(o)}
                  className="mr-2 text-neutral-700 dark:text-neutral-300"
                >
                  Edit
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={async () => {
                    if (!confirm("Eliminar orden?")) return;
                    await deleteProducto(o);
                  }}
                >
                  Delete
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
