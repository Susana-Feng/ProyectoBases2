import { Outlet, Link } from "@tanstack/react-router";
import { useState } from "react";
import { motion } from "motion/react";
import {
  Sidebar,
  SidebarBody,
  SidebarLink,
} from "@/components/ui/sidebar";
import {
  Upload,
  Users,
  Package,
  ShoppingCart,
  List,
} from "lucide-react";
import { ModeToggle } from "@/components/mode-toggle";
import { SidebarContextProvider } from "@/contexts/sidebar-context";

export default function RootLayout() {
  // Always start collapsed, no persistence needed
  const [open, setOpen] = useState(false);

  const links = [
    {
      label: "Cargar Excel",
      href: "/",
      icon: <Upload className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
    },
    {
      label: "Clientes",
      href: "/clientes",
      icon: <Users className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
    },
    {
      label: "Productos",
      href: "/productos",
      icon: <Package className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
    },
    {
      label: "Órdenes",
      href: "/ordenes",
      icon: <ShoppingCart className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
    },
    {
      label: "Detalles",
      href: "/orden-detalles",
      icon: <List className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
    },
  ];

  return (
    <SidebarContextProvider>
      <div className="flex h-screen overflow-hidden bg-white dark:bg-neutral-900">
        <Sidebar open={open} setOpen={setOpen}>
          <SidebarBody className="justify-between gap-10">
            <div className="flex flex-1 flex-col overflow-x-hidden overflow-y-auto">
              {open ? <Logo /> : <LogoIcon />}
              <div className="mt-8 flex flex-col gap-2">
                {links.map((link, idx) => (
                  <SidebarLink key={idx} link={link} />
                ))}
              </div>
            </div>
            
            {/* Theme toggle at the bottom */}
            <div className={`pb-4 ${open ? 'px-2' : 'flex justify-center'}`}>
              <ModeToggle isExpanded={open} />
            </div>
          </SidebarBody>
        </Sidebar>

        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </SidebarContextProvider>
  );
}

export const Logo = () => {
  return (
    <Link
      to="/"
      className="relative z-20 flex items-center space-x-2 py-1 text-sm font-normal text-black"
    >
      <div className="h-5 w-6 shrink-0 rounded-tl-lg rounded-tr-sm rounded-br-lg rounded-bl-sm bg-gradient-to-br from-blue-600 to-blue-400 dark:from-blue-400 dark:to-blue-600" />
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="font-medium whitespace-pre text-black dark:text-white"
      >
        MySQL Loader
      </motion.span>
    </Link>
  );
};

export const LogoIcon = () => {
  return (
    <Link
      to="/"
      className="relative z-20 flex items-center space-x-2 py-1 text-sm font-normal text-black"
    >
      <div className="h-5 w-6 shrink-0 rounded-tl-lg rounded-tr-sm rounded-br-lg rounded-bl-sm bg-gradient-to-br from-blue-600 to-blue-400 dark:from-blue-400 dark:to-blue-600" />
    </Link>
  );
};
