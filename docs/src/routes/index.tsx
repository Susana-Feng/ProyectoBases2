import { createFileRoute, redirect } from "@tanstack/react-router";
import { i18n } from "@/lib/i18n";

export const Route = createFileRoute("/")({
  loader: () => {
    throw redirect({
      href: `/${i18n.defaultLanguage}`,
    });
  },
});

