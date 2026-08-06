import { ClerkProvider, UserButton } from "@clerk/nextjs";
import type { Metadata } from "next";
import Link from "next/link";

import { activeBrand } from "@/lib/api";
import "@/lib/server-auth";

import "./globals.css";

// Clerk turns on with its publishable key and off without it (mirrors middleware.ts). The API is
// what fails closed; this flag only decides whether the *pages* ask people to sign in.
const clerkConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

export const metadata: Metadata = {
  title: "BrandCortex — review",
  description: "Compose, review and publish brand content.",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Read the tenant rather than hardcode it. A dashboard with "ThaiSwim" written into a component is
  // a dashboard that needs editing to onboard brand #2.
  const brand = await activeBrand();

  const page = (
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
              {clerkConfigured && <UserButton />}
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );

  return clerkConfigured ? <ClerkProvider>{page}</ClerkProvider> : page;
}
