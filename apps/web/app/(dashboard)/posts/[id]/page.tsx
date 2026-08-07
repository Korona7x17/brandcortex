import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError, api, cardUrl } from "@/lib/api-server";

import { Reviewer } from "./reviewer";

export const dynamic = "force-dynamic";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default async function PostPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let post;
  try {
    post = await api.getPost(id);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }

  const features = post.features;

  return (
    <>
      <p className="note" style={{ marginBottom: 18 }}>
        <Link href="/">← queue</Link>
        {"  ·  "}
        <span className="badge" data-status={post.status}>{post.status}</span>
      </p>

      <div className="detail">
        <div>
          <div className="panel">
            <h2>Card — the bytes that publish</h2>
            {post.asset_storage_key ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img className="card" src={cardUrl(post.id)} alt="captured card" />
            ) : (
              <p className="note">No card captured. This post cannot be approved.</p>
            )}
          </div>

          <div className="panel">
            <h2>What the card asserts</h2>
            {/* Shown next to the caption asserting them. The numeric check already guarantees they
                agree; seeing them is what lets a reviewer confirm this is the *right* card, which no
                check can do. */}
            <dl className="facts">
              {Object.entries(post.facts)
                .filter(([, value]) => value !== null && typeof value !== "object")
                .map(([key, value]) => (
                  <FactRow key={key} label={key} value={String(value)} />
                ))}
            </dl>
          </div>

          {features && (
            <div className="panel">
              <h2>Captured features</h2>
              <dl className="facts">
                <FactRow label="hook" value={features.hook_style ?? "—"} />
                <FactRow label="locale" value={features.locale ?? "—"} />
                <FactRow label="wow" value={features.wow_factor?.toFixed(3) ?? "—"} />
                <FactRow label="caption len" value={String(features.caption_length ?? "—")} />
                <FactRow
                  label="posted"
                  value={
                    features.post_hour === null
                      ? "not yet"
                      : `${WEEKDAYS[features.post_weekday ?? 0]} ${String(features.post_hour).padStart(2, "0")}:00 local`
                  }
                />
                {features.intro_line && <FactRow label="intro" value={features.intro_line} />}
              </dl>
              <p className="note">
                Recorded from post #1 so the learning loop has history when it switches on. They cannot
                be reconstructed later.
              </p>
            </div>
          )}
        </div>

        <div>
          <Reviewer initial={post} />

          <div className="panel">
            <h2>Attribution</h2>
            <dl className="facts">
              <FactRow label="campaign" value={post.utm_campaign ?? "—"} />
              <FactRow label="content id" value={post.content_id} />
              {post.channel_post_id && <FactRow label="channel post" value={post.channel_post_id} />}
              {post.channel_comment_id && (
                <FactRow label="channel comment" value={post.channel_comment_id} />
              )}
              {post.published_at && (
                <FactRow label="published" value={new Date(post.published_at).toLocaleString()} />
              )}
            </dl>
            {post.latest_insight ? (
              <p className="note">
                Latest snapshot {new Date(post.latest_insight.captured_at).toLocaleString()} · reach{" "}
                {post.latest_insight.reach ?? "—"} · shares {post.latest_insight.shares ?? "—"} · UTM
                sessions {post.latest_insight.utm_sessions ?? "—"}
              </p>
            ) : (
              <p className="note">
                No performance snapshot yet. The north star is UTM-tracked sessions and amplification —
                reactions are recorded but never targeted.
              </p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function FactRow({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}
