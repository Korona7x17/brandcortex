"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { ApiError, api, type PostDetail, type Variant } from "@/lib/api";

/**
 * Pick a framing.
 *
 * These are angles on the same facts, not rewordings — the sweep across strokes, longevity at this
 * age, the club, one standout swim. Every one has already passed the numeric check and the voice
 * rules, so choosing between them is a judgment about what to notice, which is the part a person is
 * actually better at.
 *
 * Angles that did not fit are shown greyed with the reason rather than hidden. A swimmer with one
 * gold has no sweep to describe, and that is worth seeing; an angle failing the numeric check is a
 * template bug, and hiding it is how that survives for months.
 */
export function Variants({ post, onChange }: { post: PostDetail; onChange: (p: PostDetail) => void }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, start] = useTransition();

  const offered = post.variants.filter((v) => v.post_text);
  if (offered.length < 2) return null;

  const choose = (variant: Variant) =>
    start(async () => {
      setError(null);
      try {
        const updated = await api.chooseVariant(post.id, variant.angle);
        onChange(updated);
        router.refresh();
      } catch (e) {
        setError(e instanceof ApiError ? e.reasons.join("; ") : (e as Error).message);
      }
    });

  const locked = post.status === "published";

  return (
    <div className="panel">
      <h2>
        {offered.length} ways to say it
        {locked && " — published, locked"}
      </h2>

      <div className="variants">
        {post.variants.map((variant) => {
          const unavailable = !variant.post_text;
          return (
            <button
              key={variant.angle}
              className="variant"
              data-chosen={variant.chosen}
              disabled={unavailable || locked || pending}
              onClick={() => choose(variant)}
            >
              <span className="head">
                <span className="angle">{variant.angle}</span>
                {variant.hook_style && <span>{variant.hook_style}</span>}
                <span>· {variant.origin}</span>
                {variant.chosen && <span style={{ color: "var(--accent)" }}>· chosen</span>}
              </span>

              {unavailable ? (
                <p className="why">not offered — {variant.rejected.join("; ")}</p>
              ) : (
                <p className="body">{variant.post_text}</p>
              )}
            </button>
          );
        })}
      </div>

      {error && (
        <div className="reasons">
          <strong>Could not switch</strong>
          <ul>
            <li>{error}</li>
          </ul>
        </div>
      )}

      <p className="note">
        Each has already passed the numeric check and the voice rules. Which framing you pick is
        recorded — it is the cleanest signal the learning loop gets.
      </p>
    </div>
  );
}
