"use client";

import { useEffect, useState, useTransition } from "react";

import { ApiError, api, type PostDetail } from "@/lib/api";

/**
 * Assign a slot, or publish now.
 *
 * Open decision #5 — whether Phase 1 always schedules or publishes on approval — is deliberately
 * left to the reviewer here rather than settled in code. Both buttons are present, the scheduler's
 * suggestion is prefilled, and the reasons behind it are shown so overriding it is an informed act
 * rather than a shrug.
 */
export function Schedule({ post, onChange }: { post: PostDetail; onChange: (p: PostDetail) => void }) {
  const [when, setWhen] = useState("");
  const [reasons, setReasons] = useState<string[]>([]);
  const [relaxed, setRelaxed] = useState<string[]>([]);
  const [tz, setTz] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, start] = useTransition();

  const schedulable = post.status === "approved" || post.status === "scheduled";

  useEffect(() => {
    if (!schedulable || when) return;
    let live = true;
    api
      .suggestedSlot(post.id)
      .then((slot) => {
        if (!live) return;
        setWhen(toLocalInput(slot.at));
        setReasons(slot.reasons);
        setRelaxed(slot.relaxed);
        setTz(slot.timezone);
      })
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [post.id, schedulable, when]);

  if (!schedulable) return null;

  const act = (fn: () => Promise<PostDetail>) =>
    start(async () => {
      setError(null);
      try {
        onChange(await fn());
      } catch (e) {
        setError(e instanceof ApiError ? e.reasons.join("; ") : (e as Error).message);
      }
    });

  return (
    <div className="panel">
      <h2>
        {post.status === "scheduled" ? "Scheduled" : "When should this go out?"}
      </h2>

      {post.status === "scheduled" && post.scheduled_for && (
        <p className="copy" style={{ marginBottom: 12 }}>
          {new Date(post.scheduled_for).toLocaleString()}
        </p>
      )}

      <div className="field">
        <label htmlFor="when">Publish at {tz && `· suggested in ${tz}`}</label>
        <input
          id="when"
          type="datetime-local"
          value={when}
          onChange={(e) => setWhen(e.target.value)}
          disabled={pending}
        />
      </div>

      {reasons.length > 0 && (
        <ul className="note" style={{ margin: "0 0 4px", paddingLeft: 18 }}>
          {reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
          {relaxed.map((r) => (
            <li key={r} style={{ color: "var(--warn)" }}>{r}</li>
          ))}
        </ul>
      )}

      <div className="actions">
        <button
          onClick={() => act(() => api.schedule(post.id, new Date(when).toISOString()))}
          disabled={pending || !when}
        >
          {post.status === "scheduled" ? "Reschedule" : "Schedule"}
        </button>
        <button className="primary" onClick={() => act(() => api.publish(post.id))} disabled={pending}>
          Publish now
        </button>
      </div>

      {error && (
        <div className="reasons">
          <strong>Not scheduled</strong>
          <ul>
            <li>{error}</li>
          </ul>
        </div>
      )}
    </div>
  );
}

/** `datetime-local` wants `YYYY-MM-DDTHH:mm` in the viewer's own zone, not an ISO instant. */
function toLocalInput(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
