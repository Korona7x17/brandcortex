"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { ApiError, api, type PostDetail } from "@/lib/api";
import { diffWords } from "@/lib/diff";

import { CopyButton } from "./copy";
import { Schedule } from "./schedule";
import { Variants } from "./variants";

/**
 * The approval gate, Phase 1 style: read the caption against the card, edit if needed, approve,
 * publish.
 *
 * No check runs here. The server rejects an ungrounded number, a link in the body, or a stripped
 * campaign, and this component's whole job on rejection is to show what it said. Validating locally
 * would drift from the server's answer, and the drift would always favour this side — because this
 * is the one the reviewer sees.
 */
export function Reviewer({ initial }: { initial: PostDetail }) {
  const router = useRouter();
  const [post, setPost] = useState(initial);
  const [caption, setCaption] = useState(initial.post_text ?? "");
  const [reasons, setReasons] = useState<string[]>([]);
  const [nudge, setNudge] = useState("");
  const [pending, start] = useTransition();

  const dirty = caption !== (post.post_text ?? "");
  const terminal = post.status === "published";

  const run = (action: () => Promise<PostDetail>) =>
    start(async () => {
      setReasons([]);
      try {
        const updated = await action();
        setPost(updated);
        setCaption(updated.post_text ?? "");
        router.refresh();
      } catch (error) {
        setReasons(
          error instanceof ApiError ? error.reasons : [(error as Error).message ?? "unknown error"],
        );
      }
    });

  const adopt = (updated: PostDetail) => {
    setPost(updated);
    setCaption(updated.post_text ?? "");
    setReasons([]);
  };

  return (
    <>
      <div className="panel">
        <h2>Rewrite</h2>
        <div className="field">
          <label htmlFor="nudge">Direction for this post only</label>
          <input
            id="nudge"
            type="search"
            value={nudge}
            onChange={(e) => setNudge(e.target.value)}
            placeholder="shorter · lead with her age · make it about the comeback"
            disabled={terminal || pending}
          />
        </div>
        <div className="actions">
          <button
            onClick={() => run(() => api.regenerate(post.id, nudge))}
            disabled={terminal || pending}
          >
            {pending ? "Writing…" : "Regenerate all angles"}
          </button>
          <span className="note">
            Replaces every variant. A direction steers the writing; it cannot loosen a check.
          </span>
        </div>
      </div>

      <Variants post={post} onChange={adopt} />

      <div className="panel">
        <h2>
          Caption {dirty && "— unsaved"}
          <span style={{ float: "right" }}>
            {post.post_text && <CopyButton text={post.post_text} />}
          </span>
        </h2>
        {terminal ? (
          <p className="copy">{post.post_text}</p>
        ) : (
          <textarea
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            spellCheck={false}
            disabled={pending}
          />
        )}

        <div className="actions">
          {!terminal && (
            <button
              onClick={() => run(() => api.edit(post.id, { post_text: caption }))}
              disabled={pending || !dirty}
            >
              Save edit
            </button>
          )}
          {post.status === "draft" && (
            <button className="primary" onClick={() => run(() => api.approve(post.id))} disabled={pending || dirty}>
              Approve
            </button>
          )}
          {(post.status === "approved" || post.status === "scheduled") && (
            <button className="primary" onClick={() => run(() => api.publish(post.id))} disabled={pending}>
              Publish now
            </button>
          )}
          {post.status === "failed" && (
            <span className="note">Edit the caption to return this to the queue.</span>
          )}
          {dirty && post.status === "draft" && <span className="note">Save before approving.</span>}
        </div>

        {reasons.length > 0 && (
          <div className="reasons">
            <strong>Rejected</strong>
            <ul>
              {reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
        )}

        {post.error && reasons.length === 0 && (
          <div className="reasons">
            <strong>Last failure</strong>
            <ul>
              <li>{post.error}</li>
            </ul>
          </div>
        )}
      </div>

      <Schedule post={post} onChange={adopt} />

      <div className="panel">
        <h2>
          First comment — carries the link
          <span style={{ float: "right" }}>
            {post.first_comment_text && <CopyButton text={post.first_comment_text} />}
          </span>
        </h2>
        <p className="comment">{post.first_comment_text ?? "—"}</p>
        <p className="note">
          The link never goes in the caption: photo posts out-reach link posts, and comments are exempt
          from Meta’s body-link cap.
        </p>
      </div>

      {post.edited && post.generated.post_text && (
        <div className="panel">
          <h2>Changed from the engine’s draft</h2>
          <p className="copy diff">
            {diffWords(post.generated.post_text, post.post_text ?? "").map((chunk, index) =>
              chunk.kind === "same" ? (
                <span key={index}>{chunk.value}</span>
              ) : chunk.kind === "added" ? (
                <ins key={index}>{chunk.value}</ins>
              ) : (
                <del key={index}>{chunk.value}</del>
              ),
            )}
          </p>
          <p className="note">
            What a reviewer changes is the clearest signal available about where the engine is off.
          </p>
        </div>
      )}
    </>
  );
}
