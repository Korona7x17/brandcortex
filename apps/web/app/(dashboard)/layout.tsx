import { UserButton } from "@clerk/nextjs";
import Link from "next/link";

import { activeBrand } from "@/lib/api-server";

// Clerk components render only when the provider exists (see the root layout).
const clerkConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  // Read the tenant rather than hardcode it. A dashboard with "ThaiSwim" written into a component is
  // a dashboard that needs editing to onboard brand #2.
  const brand = await activeBrand();

  return (
    <div className="wrap">
      <header className="site">
        <Link href="/" className="mark">
          <span className="mark-dot" aria-hidden />
          <span>
            Brand<span style={{ color: "var(--mute-2)" }}>Cortex</span>
          </span>
        </Link>

        {brand ? (
          <span className="tenant">
            <strong>{brand.display_name}</strong>
            <span className="tenant-meta">
              {brand.channels.join(", ") || "no channel"} · {brand.timezone}
            </span>
          </span>
        ) : (
          <span className="tenant tenant-none">no tenant configured</span>
        )}

        <span className="spacer" />
        <nav className="site-nav">
          <Link href="/">Queue</Link>
          {brand && <Link href="/new">New card</Link>}
          {brand && <Link href="/settings/voice">Voice</Link>}
          {clerkConfigured && <UserButton />}
        </nav>
      </header>
      {children}
    </div>
  );
}
