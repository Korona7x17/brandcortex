/**
 * Image proxy for captured cards.
 *
 * The dashboard's `<img>` tags cannot carry the Clerk session token, and drafts are not public
 * content, so the API's card route is as locked as every other. This handler runs on the app
 * server, where the session *is* available, and streams the bytes through.
 */
import { NextResponse } from "next/server";

import { API_URL, sessionToken } from "@/lib/api-server";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const token = await sessionToken();

  const upstream = await fetch(`${API_URL}/posts/${encodeURIComponent(id)}/card`, {
    headers: token ? { authorization: `Bearer ${token}` } : {},
    cache: "no-store",
  });
  if (!upstream.ok || !upstream.body) {
    return new NextResponse(null, { status: upstream.status });
  }
  return new NextResponse(upstream.body, {
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "image/png",
      "cache-control": "private, no-store",
    },
  });
}
