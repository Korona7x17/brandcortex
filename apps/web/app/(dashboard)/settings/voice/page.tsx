import { activeBrand, brandApi } from "@/lib/api";

import { BriefEditor } from "./editor";

export const dynamic = "force-dynamic";

export default async function VoiceSettings() {
  const brand = await activeBrand();
  if (!brand) return <div className="empty">No tenant configured.</div>;

  const brief = await brandApi.getBrief(brand.brand);
  return <BriefEditor brand={brand} initial={brief} />;
}
