import { loader } from "fumadocs-core/source";
import * as icons from "lucide-static";
import { create, docs } from "@/.source";
import { i18n } from "@/lib/i18n";

export const source = loader({
  i18n,
  source: await create.sourceAsync(docs.doc, docs.meta),
  baseUrl: "/docs",
  icon(icon) {
    if (!icon) {
      return;
    }

    // biome-ignore lint/performance/noDynamicNamespaceImportAccess: necessary for dynamic icon access
    if (icon in icons) return icons[icon as keyof typeof icons];
  },
});
