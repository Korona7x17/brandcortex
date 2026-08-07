/**
 * The server-side entry to the API client. Every server component and route handler that talks to
 * the API must import it from here, not from `@/lib/api`.
 *
 * `lib/api.ts` is shared with client components, so it may not import `@clerk/nextjs/server` — that
 * poisons a client bundle at build time even behind a runtime guard. The server's token source is
 * therefore *registered* into it, and this module is where that happens.
 *
 * Registration used to be a bare side-effect import in the root layout, and that was wrong: it made
 * correctness depend on an unrelated module being evaluated first. On a client-side navigation Next
 * renders only the changed segment, so a cold instance whose first request was a soft nav had never
 * evaluated the layout — the call went out with no Authorization header and the API answered 401.
 * A hard refresh rendered the layout, registered the source, and the same page then worked, which is
 * exactly what made it look intermittent.
 *
 * Re-exporting the client from the module that registers the source removes the ordering question:
 * you cannot obtain `api` on the server without having run the registration.
 */
import "server-only";

import { auth } from "@clerk/nextjs/server";

import { registerServerTokenSource } from "./api";

registerServerTokenSource(async () => {
  // `auth()` reads per-request context (AsyncLocalStorage), so one process-wide registration is
  // safe: each call still resolves the session of the request it runs in.
  const { getToken } = await auth();
  return getToken();
});

export * from "./api";
