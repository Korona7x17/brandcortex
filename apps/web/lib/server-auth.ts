/**
 * The server half of `sessionToken()` — see the note in lib/api.ts.
 *
 * Importing this module registers Clerk's `auth()` as the token source for every server-side API
 * call. `auth()` reads per-request context (AsyncLocalStorage), so one process-wide registration
 * is safe: each call still resolves the session of the request it runs in. Imported for its side
 * effect from the root layout, which every page renders through, and from the card proxy route.
 */
import "server-only";

import { auth } from "@clerk/nextjs/server";

import { registerServerTokenSource } from "./api";

registerServerTokenSource(async () => {
  try {
    return await (await auth()).getToken();
  } catch {
    // Outside clerkMiddleware (misconfigured matcher) there is no request context; a null token
    // fails at the API with 401 rather than crashing the render.
    return null;
  }
});
