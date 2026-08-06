import { activeBrand } from "@/lib/api";

import { Composer } from "./composer";

export const dynamic = "force-dynamic";

export default async function NewCard() {
  const brand = await activeBrand();

  if (!brand) {
    return <div className="empty">No tenant configured — seed a brand_config row first.</div>;
  }
  if (!brand.connected) {
    return (
      <div className="empty">
        <p>No source adapter registered for {brand.display_name}.</p>
        <p className="note">The API logs a bootstrap failure when this happens; check it.</p>
      </div>
    );
  }

  return <Composer brand={brand} />;
}
