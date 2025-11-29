import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableCaption } from "@/components/ui/table";
import DarkToggle from "@/components/DarkToggle";
import { ArrowBigLeftDash, ArrowBigRightDash } from 'lucide-react';
import { EditOrderDialog } from "@/components/EditOrderDialog";
import { CreateOrderDialog } from "@/components/CreateOrderDialog";
import { API_BASE_URL } from "@/lib/env";

// --- Nodo Producto ---
export type Producto = {
  id: string;              // Propiedad del nodo Producto
  nombre: string;
  categoria: string;
  sku?: string;
  codigo_alt?: string;
  codigo_mongo?: string;
};

// --- Nodo Cliente ---
export type Cliente = {
  id: string;              // Propiedad del nodo Cliente
  nombre: string;
  genero: "M" | "F" | "Otro" | "Masculino" | "Femenino";
  pais: string;
};

// --- Relación CONTIENE ---
export type Contiene = {
  cantidad: number;
  precio_unit: number;
  producto: Producto;      // Nodo destino de la relación
};

// --- Nodo Orden ---
export type Orden = {
  id?: string;             // Propiedad del nodo Orden (en Neo4j)
  fecha: string;           // ISO (datetime en Neo4j)
  canal: "WEB" | "TIENDA";
  moneda: "CRC" | "USD";
  total: number;
  
  // Relaciones
  cliente: Cliente;        // (Cliente)-[:REALIZO]->(Orden)
  items: Contiene[];       // (Orden)-[:CONTIENE]->(Producto)
  
  // Atributo opcional no estructural
  metadatos?: { cupon?: string } | null;
};
const rutaBase = `${API_BASE_URL}/orders`;

export default function Orders() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [skip, setSkip] = useState<number>(0);
  const [limit, setLimit] = useState<number>(10);
  // Track whether the user explicitly changed the page size so we don't
  // override their choice when the backend returns a `count`.
  const [userSetLimit, setUserSetLimit] = useState<boolean>(false);
  const [total, setTotal] = useState<number | null>(null);
  const [editingOrder, setEditingOrder] = useState<any | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [hasMore, setHasMore] = useState<boolean>(false);


  const currentPage = limit > 0 ? Math.floor(skip / limit) + 1 : 1;
  const knownTotal = typeof total === "number" ? Math.max(total, skip + orders.length) : undefined;
  const totalPages = typeof knownTotal === "number" && limit > 0 ? Math.max(1, Math.ceil(knownTotal / limit)) : undefined;

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

    // En tu componente Orders, corrige la función handleSave:
    async function handleSave(edited: any) {
    try {
        setLoading(true);
        setError(null);


        const res = await fetch(`${rutaBase}/${edited.id}`, {
        method: "PUT", // ✅ Cambiar a PUT
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

        console.log("🔄 Creando orden:", newOrder);

        const res = await fetch(rutaBase, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newOrder),
        });

        if (!res.ok) {
        const errorData = await res.json().catch(() => null);
        console.error("❌ Error del backend:", errorData);
        throw new Error(errorData?.detail || `HTTP ${res.status}`);
        }

        
        await loadOrders(skip, limit);
    } catch (err: any) {

        setError(err?.message || String(err));
    } finally {
        setLoading(false);
    }
    }

    async function loadOrders(skipArg?: number, limitArg?: number) {
    setLoading(true);
    setError(null);
    try {
      const userLimit = typeof limitArg === "number" ? limitArg : limit;
      const userSkip = typeof skipArg === "number" ? skipArg : skip;

      // Traer todas las órdenes (limit infinito o muy alto)
      const url = `${rutaBase}/?skip=0&limit=9999`;
      const data = await fetchJson(url);

      const allOrders = data?.data ?? [];
      const totalOrders = allOrders.length;

      // Aplicar paginación local según skip y limit del usuario
      const pagedOrders = allOrders.slice(userSkip, userSkip + userLimit);

      // Formatear para el frontend
      const formatted = pagedOrders.map((o: any) => ({
        _id: o.id,
        id: o.id,
        fecha: o.fecha,
        canal: o.canal,
        moneda: o.moneda,
        total: o.total,
        cliente: o.cliente,
        items: (o.items || []).map((it: any) => ({
          producto_id: it.producto_id,
          producto_nombre: it.producto_nombre,
          categoria_id: it.categoria_id,
          categoria: it.categoria,
          cantidad: it.cantidad,
          precio_unit: it.precio_unit,
          subtotal: it.subtotal,
          producto: {
            id: it.producto_id,
            nombre: it.producto_nombre,
            categoria: it.categoria
          }
        }))
      }));

      // Actualizar estado
      setOrders(formatted);
      setTotal(totalOrders);  // total de órdenes
      setSkip(userSkip);
      setLimit(userLimit);
      setHasMore(userSkip + userLimit < totalOrders);

    } catch (err: any) {
      console.error("Error al cargar órdenes:", err);
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
        setUserSetLimit(true);
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
                {new Date(o.fecha).toLocaleDateString()}
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

                {(o.items || []).reduce((agrupados: any[], item: any) => {
                    // Buscar si ya existe este producto en los agrupados
                    const existente = agrupados.find(ag => ag.producto_id === item.producto_id);
                    if (existente) {
                    existente.cantidad_total += item.cantidad;
                    } else {
                    agrupados.push({
                        producto_id: item.producto_id,
                        producto_nombre: item.producto_nombre || item.producto?.nombre,
                        cantidad_total: item.cantidad,
                        precio_unit: item.precio_unit
                    });
                    }
                    return agrupados;
                }, []).map((itemAgrupado: any, i: number) => (
                    <div key={i} className="text-sm">
                    {itemAgrupado.producto_nombre} — {itemAgrupado.cantidad_total} × {itemAgrupado.precio_unit}
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
