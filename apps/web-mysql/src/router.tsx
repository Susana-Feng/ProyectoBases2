import { createRootRoute, createRoute, createRouter } from "@tanstack/react-router";
import RootLayout from "./routes/__root";
import IndexPage from "./routes/index";
import ClientesPage from "./routes/clientes";
import ProductosPage from "./routes/productos";
import OrdenesPage from "./routes/ordenes";
import OrdenDetallesPage from "./routes/orden-detalles";

// Root route
const rootRoute = createRootRoute({
  component: RootLayout,
});

// Index route
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: IndexPage,
});

// Clientes route
const clientesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/clientes",
  component: ClientesPage,
});

// Productos route
const productosRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/productos",
  component: ProductosPage,
});

// Órdenes route
const ordenesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/ordenes",
  component: OrdenesPage,
});

// Orden Detalles route
const ordenDetallesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/orden-detalles",
  component: OrdenDetallesPage,
});

// Create route tree
const routeTree = rootRoute.addChildren([
  indexRoute,
  clientesRoute,
  productosRoute,
  ordenesRoute,
  ordenDetallesRoute,
]);

// Create router
export const router = createRouter({ routeTree });

// Register router for type safety
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
