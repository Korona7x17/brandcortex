/**
 * Typed client for the BrandCortex API.
 *
 * Every rule about what may be published lives on the server — numeric grounding, link placement,
 * voice, the state machine. This module deliberately re-implements none of them. A UI that validated
 * locally would drift from the API's answer, and the drift would always favour the UI, because that
 * is the one a reviewer sees.
 *
 * So the client's only job with a rejection is to render it. A 422 carries the reasons the server
 * gave; a 409 means the post is not in a state the action applies to.
 */

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type PostStatus = "draft" | "approved" | "scheduled" | "published" | "failed";

export interface PostSummary {
  id: string;
  content_id: string;
  brand: string;
  channel: string;
  status: PostStatus;
  source_type: string | null;
  post_text: string | null;
  first_comment_text: string | null;
  asset_storage_key: string | null;
  utm_campaign: string | null;
  scheduled_for: string | null;
  approved_at: string | null;
  published_at: string | null;
  channel_post_id: string | null;
  channel_comment_id: string | null;
  error: string | null;
  created_at: string;
  edited: boolean;
}

export interface PostFeatures {
  source_type: string | null;
  locale: string | null;
  intro_line: string | null;
  hook_style: string | null;
  caption_length: number | null;
  hashtag_set: string | null;
  post_hour: number | null;
  post_weekday: number | null;
  wow_factor: number | null;
  dimensions: Record<string, string | number | boolean>;
}

export interface Insight {
  captured_at: string;
  reach: number | null;
  impressions: number | null;
  reactions: number | null;
  comments: number | null;
  shares: number | null;
  saves: number | null;
  link_clicks: number | null;
  utm_sessions: number | null;
}

export interface Variant {
  angle: string;
  position: number;
  post_text: string | null;
  first_comment_text: string | null;
  hook_style: string | null;
  intro_line: string | null;
  origin: "template" | "model";
  model: string | null;
  rejected: string[];
  chosen: boolean;
}

export interface PostDetail extends PostSummary {
  variants: Variant[];
  generated: { post_text: string | null; first_comment_text: string | null };
  facts: Record<string, unknown>;
  features: PostFeatures | null;
  latest_insight: Insight | null;
}

/** A rejection the reviewer needs to read, not a bug. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly reasons: string[],
  ) {
    super(reasons.join("; "));
    this.name = "ApiError";
  }
}

/**
 * The caller's Clerk session token, from whichever side this request is running on. Null when
 * Clerk is not configured (local development), in which case the API is expected to be running
 * with its own explicit `AUTH_DISABLED=true`; an API without either answers 503, not open.
 *
 * The two sides get their token differently, and this module is imported by both — so it may not
 * import `@clerk/nextjs/server`, which poisons a client bundle at build time even behind a runtime
 * guard. The browser asks the Clerk instance on `window`; the server side is *registered* by
 * `lib/api-server.ts`, a `server-only` module that closes over `auth()` without this file ever
 * naming it, and that re-exports everything here so server code cannot reach `api` without it.
 *
 * An unregistered server call is a wiring bug, not a signed-out visitor, so it raises rather than
 * returning null. Silently sending no token produced a 401 that read as an auth problem and sent
 * two debugging sessions after the wrong thing.
 */
let serverTokenSource: (() => Promise<string | null>) | null = null;

export function registerServerTokenSource(source: () => Promise<string | null>) {
  serverTokenSource = source;
}

export async function sessionToken(): Promise<string | null> {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) return null;
  if (typeof window === "undefined") {
    if (!serverTokenSource) {
      throw new Error(
        "no server token source: server components and route handlers must import the API from" +
          " '@/lib/api-server', not '@/lib/api'",
      );
    }
    return serverTokenSource();
  }
  type ClerkOnWindow = { session?: { getToken(): Promise<string | null> } };
  return (await (window as { Clerk?: ClerkOnWindow }).Clerk?.session?.getToken()) ?? null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await sessionToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(response.status, await readReasons(response));
  }
  return (await response.json()) as T;
}

/**
 * Rejections arrive in two shapes: `{detail: {reasons: [...]}}` when a check refused the content,
 * and `{detail: "..."}` for everything else. Both are worth showing verbatim — the server's message
 * names the number that was unsupported, or the state the post is actually in.
 */
async function readReasons(response: Response): Promise<string[]> {
  try {
    const body = await response.json();
    const detail = body?.detail;
    if (Array.isArray(detail?.reasons)) return detail.reasons as string[];
    if (typeof detail === "string") return [detail];
    return [JSON.stringify(detail ?? body)];
  } catch {
    return [`${response.status} ${response.statusText}`];
  }
}

export const api = {
  listPosts: (params: { brand?: string; status?: string } = {}) => {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => Boolean(v)) as [string, string][],
    );
    return request<PostSummary[]>(`/posts${query.size ? `?${query}` : ""}`);
  },

  getPost: (id: string) => request<PostDetail>(`/posts/${id}`),

  insights: (id: string) => request<Insight[]>(`/posts/${id}/insights`),

  edit: (id: string, body: { post_text?: string; first_comment_text?: string }) =>
    request<PostDetail>(`/posts/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  approve: (id: string) => request<PostDetail>(`/posts/${id}/approve`, { method: "POST" }),

  publish: (id: string) => request<PostDetail>(`/posts/${id}/publish`, { method: "POST" }),

  suggestedSlot: (id: string) =>
    request<{ at: string; reasons: string[]; relaxed: string[]; timezone: string; booked: number }>(
      `/posts/${id}/suggested-slot`,
    ),

  schedule: (id: string, when: string) =>
    request<PostDetail>(`/posts/${id}/schedule`, {
      method: "POST",
      body: JSON.stringify({ when }),
    }),

  regenerate: (id: string, nudge?: string) =>
    request<PostDetail>(`/posts/${id}/regenerate`, {
      method: "POST",
      body: JSON.stringify({ nudge: nudge?.trim() || null }),
    }),

  chooseVariant: (id: string, angle: string) =>
    request<PostDetail>(`/posts/${id}/variants/${encodeURIComponent(angle)}/choose`, {
      method: "POST",
    }),
};

/** The captured card — the exact bytes that publish, not the brand's live render. Served through
 *  the app's own `/card/[id]` proxy rather than the API directly: an `<img>` cannot carry the
 *  session token, so the proxy attaches it server-side (app/card/[id]/route.ts). */
export const cardUrl = (id: string) => `/card/${id}`;

// --- tenant ------------------------------------------------------------------------------------

export interface SourceTypeField {
  name: string;
  label: string;
  options: string[];
}

export interface SourceType {
  key: string;
  label: string;
  searchable: boolean;
  search_hint?: string;
  fields: SourceTypeField[];
}

export interface Brand {
  brand: string;
  display_name: string;
  site_url: string | null;
  timezone: string | null;
  default_locale: string | null;
  supported_locales: string[];
  channels: string[];
  source_types: SourceType[];
  connected: boolean;
}

export interface Subject {
  source_type: string;
  key: string;
  label: string;
  sublabel: string | null;
  hint: string | null;
  params: Record<string, string>;
}

/**
 * Which tenant this dashboard is showing.
 *
 * Read from the API, never hardcoded — the same rule the Python core follows, carried across the
 * language boundary. `NEXT_PUBLIC_BRAND` pins it when more than one is configured; otherwise the
 * single configured brand is the answer, and the day there are two without a pin, that is a
 * deployment that has not decided yet rather than something to guess at.
 */
export async function activeBrand(): Promise<Brand | null> {
  const pinned = process.env.NEXT_PUBLIC_BRAND;
  try {
    const brands = await request<{ brand: string; display_name: string }[]>("/brands");
    const key = pinned ?? (brands.length === 1 ? brands[0].brand : null);
    return key ? await request<Brand>(`/brands/${key}`) : null;
  } catch {
    return null;
  }
}

export interface WriterAngle {
  key: string;
  instruction: string;
}

export interface WriterBrief {
  guidance: string;
  angles: WriterAngle[];
  examples: string[];
  max_variants: number;
  voice: Record<string, unknown>;
  model_configured: boolean;
  model: string;
}

export const brandApi = {
  getBrief: (brand: string) => request<WriterBrief>(`/brands/${brand}/writer`),

  putBrief: (
    brand: string,
    brief: Pick<WriterBrief, "guidance" | "angles" | "examples" | "max_variants">,
  ) => request<WriterBrief>(`/brands/${brand}/writer`, { method: "PUT", body: JSON.stringify(brief) }),

  search: (brand: string, q: string) =>
    request<Subject[]>(`/brands/${brand}/search?q=${encodeURIComponent(q)}`),

  compose: (body: { brand: string; source_type: string; params: Record<string, unknown> }) =>
    request<PostDetail>("/content-items/compose", { method: "POST", body: JSON.stringify(body) }),
};

/** The brand's live render — what a card *would* look like. Only ever a preview: what publishes is
 *  the copy captured at draft time. */
export function previewUrl(brand: Brand, sourceType: string, params: Record<string, string>) {
  const site = (brand.site_url ?? "").replace(/\/$/, "");
  if (sourceType === "swimmer") {
    return `${site}/api/card/swimmer?slug=${encodeURIComponent(params.slug ?? "")}`;
  }
  const q = new URLSearchParams({
    stroke: params.stroke,
    dist: params.distance,
    gender: params.gender,
    age: params.ageGroup,
    course: params.course,
    n: params.n,
    lang: brand.default_locale ?? "th",
  });
  return `${site}/api/card/event?${q}`;
}
