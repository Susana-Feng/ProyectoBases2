import {
  createRootRoute,
  HeadContent,
  Outlet,
  Scripts,
  useParams,
} from "@tanstack/react-router";
import { TanstackProvider } from "fumadocs-core/framework/tanstack";
import { defineI18nUI } from "fumadocs-ui/i18n";
import { RootProvider } from "fumadocs-ui/provider/base";
import type * as React from "react";
import { i18n } from "@/lib/i18n";
import appCss from "@/styles/app.css?url";

const { provider } = defineI18nUI(i18n, {
  translations: {
    es: {
      displayName: "Español",
      search: "Buscar",
    },
    en: {
      displayName: "English",
      search: "Search",
    },
  },
});

export const Route = createRootRoute({
  head: () => ({
    meta: [
      {
        charSet: "utf-8",
      },
      {
        name: "viewport",
        content: "width=device-width, initial-scale=1",
      },
      {
        title: "Fumadocs on TanStack Start",
      },
    ],
    links: [{ rel: "stylesheet", href: appCss }],
  }),
  component: RootComponent,
});

function RootComponent() {
  return (
    <RootDocument>
      <Outlet />
    </RootDocument>
  );
}

function RootDocument({ children }: { children: React.ReactNode }) {
  const { lang } = useParams({ strict: false });
  return (
    <html suppressHydrationWarning lang={lang}>
      <head>
        <HeadContent />
      </head>
      <body className="flex flex-col min-h-screen">
        <TanstackProvider>
          <RootProvider i18n={provider(lang)}>{children}</RootProvider>
        </TanstackProvider>
        <Scripts />
      </body>
    </html>
  );
}
