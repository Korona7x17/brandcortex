import type { Metadata } from "next";
import Link from "next/link";

import { activeBrand } from "@/lib/api";

import "./globals.css";

export const metadata: Metadata = {
  title: "BrandCortex — review",
  description: "Compose, review and publish brand content.",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Read the tenant rather than hardcode it. A dashboard with "ThaiSwim" written into a component is
  // a dashboard that needs editing to onboard brand #2.
  const brand = await activeBrand();

  return (
    <html lang="en">
      <body>
        <div className="wrap">
          <header className="site">
            <Link href="/" className="mark">
              <span className="mark-dot" aria-hidden />
              <span>BrandCortex</span>
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
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
