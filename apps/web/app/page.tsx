import Link from "next/link";

import { api, cardUrl, type PostSummary } from "@/lib/api";

export const dynamic = "force-dynamic";

const FILTERS = [
  { label: "All", value: "" },
  { label: "Drafts", value: "draft" },
  { label: "Approved", value: "approved" },
  { label: "Published", value: "published" },
  { label: "Failed", value: "failed" },
];

export default async function Queue({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const { status = "" } = await searchParams;

  let posts: PostSummary[] = [];
  let unreachable: string | null = null;
  try {
    posts = await api.listPosts({ status });
  } catch (error) {
    unreachable = error instanceof Error ? error.message : String(error);
  }

  if (unreachable) {
    return (
      <div className="empty">
        <p>Can’t reach the API.</p>
        <p className="note">{unreachable}</p>
        <code>{`cd apps/api\nuv run uvicorn brandcortex.main:app --reload`}</code>
      </div>
    );
  }

  return (
    <>
      <nav className="filters">
        {FILTERS.map((f) => (
          <Link
            key={f.value}
            href={f.value ? `/?status=${f.value}` : "/"}
            data-active={status === f.value}
          >
            {f.label}
          </Link>
        ))}
      </nav>

      {posts.length === 0 ? <EmptyQueue status={status} /> : (
        <div className="queue">
          {posts.map((post) => (
            <Link key={post.id} href={`/posts/${post.id}`} className="card-row">
              {post.asset_storage_key ? (
                // The captured copy, not the brand's live render — what the reviewer approves is
                // byte-for-byte what publishes.
                // eslint-disable-next-line @next/next/no-img-element
                <img src={cardUrl(post.id)} alt="" />
              ) : (
                <span className="thumb-missing">no card</span>
              )}

              <div>
                <div className="meta">
                  <span>{post.source_type ?? "—"}</span>
                  <span>{post.brand} · {post.channel}</span>
                  {post.utm_campaign && <span>{post.utm_campaign}</span>}
                  <span>{new Date(post.created_at).toLocaleString()}</span>
                </div>
                <p className="caption">{post.post_text ?? post.error ?? "—"}</p>
              </div>

              <div style={{ display: "grid", gap: 6, justifyItems: "end" }}>
                <span className="badge" data-status={post.status}>{post.status}</span>
                {post.edited && <span className="badge edited">edited</span>}
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}

function EmptyQueue({ status }: { status: string }) {
  if (status) {
    return <div className="empty">Nothing with status “{status}”.</div>;
  }
  return (
    <div className="empty">
      <p>No drafts yet. The queue fills when a card is ingested.</p>
      <p className="note">
        Either poll the brand’s <code style={{ display: "inline", padding: "1px 5px" }}>card_renders</code>{" "}
        table, or push one envelope directly:
      </p>
      <code>{`# table-watch (needs BRAND_DB_URL pointing at a read-only role)
cd apps/api
uv run python -c "from brandcortex.adapters import registry; registry.bootstrap()
from brandcortex.workers.ingest_watcher import run_once
print(run_once('thaiswim'))"

# or push one envelope
curl -X POST localhost:8000/content-items \\
  -H 'content-type: application/json' -d @item.json`}</code>
    </div>
  );
}
