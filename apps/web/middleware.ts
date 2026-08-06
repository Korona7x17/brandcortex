/**
 * Every page requires a signed-in reviewer; `/sign-in` is the one exception.
 *
 * Auth turns on when the Clerk publishable key is present and off when it is not, so the app runs
 * locally before the Clerk instance exists. That is the mirror of the API's arrangement — and the
 * API is the one that fails closed. If this middleware is bypassed or misconfigured, every call the
 * pages make still dies at the API with a 401: the dashboard's auth is for people, the API's is the
 * boundary.
 */
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isSignIn = createRouteMatcher(["/sign-in(.*)"]);

const clerkConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

export default clerkConfigured
  ? clerkMiddleware(async (auth, request) => {
      if (isSignIn(request)) return;
      const { userId } = await auth();
      if (userId) return;
      // Signed out: send to /sign-in. The redirect_url return-address is kept only for deep links —
      // landing on the homepage is the overwhelmingly common case, and its sign-in URL should read
      // clean; a deep link (a post opened from elsewhere) still returns to where it pointed.
      const signIn = new URL("/sign-in", request.url);
      const { pathname, search } = request.nextUrl;
      if (pathname !== "/") signIn.searchParams.set("redirect_url", pathname + search);
      return NextResponse.redirect(signIn);
    })
  : () => NextResponse.next();

export const config = {
  matcher: [
    // Everything except static assets and Next internals; API calls go straight to FastAPI and are
    // verified there, not here.
    "/((?!_next|favicon.ico|.*\\.(?:png|jpg|svg|ico|css|js|map)$).*)",
  ],
};
