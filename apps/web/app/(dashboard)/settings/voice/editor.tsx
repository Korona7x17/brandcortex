"use client";

import { useState, useTransition } from "react";

import { ApiError, type Brand, type WriterBrief, brandApi } from "@/lib/api";

/**
 * The brief the model writes from — the brand's, not the code's.
 *
 * What is editable here is guidance, angles and examples. What is not, and never appears on this
 * page, is the set of hard rules: every number must exist in the card's facts, the link never goes
 * in the caption, the emoji ceiling holds. Those run after the model answers, so nothing typed here
 * can switch them off. That separation is what makes the page safe to expose at all.
 *
 * Examples carry the most weight. A house voice is conveyed far better by five captions its owner
 * wrote than by any description of a tone — especially when the copy is Thai and the description
 * would be in English.
 */
export function BriefEditor({ brand, initial }: { brand: Brand; initial: WriterBrief }) {
  const [guidance, setGuidance] = useState(initial.guidance);
  const [angles, setAngles] = useState(initial.angles);
  const [examples, setExamples] = useState(initial.examples);
  const [saved, setSaved] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [pending, start] = useTransition();

  const move = (index: number, by: number) => {
    const next = [...angles];
    const target = index + by;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    setAngles(next);
  };

  const save = () =>
    start(async () => {
      setErrors([]);
      setSaved(null);
      try {
        await brandApi.putBrief(brand.brand, {
          guidance,
          angles: angles.filter((a) => a.key.trim() && a.instruction.trim()),
          examples: examples.filter((e) => e.trim()),
          max_variants: initial.max_variants,
        });
        setSaved("Saved. New drafts use it immediately.");
      } catch (e) {
        setErrors(e instanceof ApiError ? e.reasons : [(e as Error).message]);
      }
    });

  return (
    <>
      <p className="note" style={{ marginBottom: 18 }}>
        How {brand.display_name} sounds. Applies to every new draft and to Regenerate.
      </p>

      {!initial.model_configured && (
        <div className="reasons" style={{ marginBottom: 18 }}>
          <strong>No model configured</strong>
          <ul>
            <li>
              ANTHROPIC_API_KEY is empty, so drafts fall back to the built-in templates and none of
              this brief is used yet. It is still worth writing — the moment a key exists,{" "}
              {initial.model} writes from exactly this.
            </li>
          </ul>
        </div>
      )}

      <div className="panel">
        <h2>Guidance</h2>
        <textarea
          value={guidance}
          onChange={(e) => setGuidance(e.target.value)}
          placeholder="Who reads these posts, and how the brand talks to them."
          style={{ minHeight: 130 }}
        />
      </div>

      <div className="panel">
        <h2>Angles — one caption written per angle</h2>
        <div className="variants">
          {angles.map((angle, index) => (
            <div className="variant" key={index} style={{ cursor: "default" }}>
              <span className="head">
                <input
                  value={angle.key}
                  onChange={(e) =>
                    setAngles(
                      angles.map((a, i) => (i === index ? { ...a, key: e.target.value } : a)),
                    )
                  }
                  style={{ width: 130, fontSize: 12 }}
                  aria-label="angle key"
                />
                <span className="spacer" style={{ flex: 1 }} />
                <button onClick={() => move(index, -1)} disabled={index === 0}>↑</button>
                <button onClick={() => move(index, 1)} disabled={index === angles.length - 1}>↓</button>
                <button onClick={() => setAngles(angles.filter((_, i) => i !== index))}>✕</button>
              </span>
              <textarea
                value={angle.instruction}
                onChange={(e) =>
                  setAngles(
                    angles.map((a, i) =>
                      i === index ? { ...a, instruction: e.target.value } : a,
                    ),
                  )
                }
                style={{ minHeight: 62 }}
              />
            </div>
          ))}
        </div>
        <div className="actions">
          <button onClick={() => setAngles([...angles, { key: "", instruction: "" }])}>
            + Add angle
          </button>
          <span className="note">
            Angles must differ in what they notice, not in wording. Keys are how a pick is attributed.
          </span>
        </div>
      </div>

      <div className="panel">
        <h2>Example captions — the register to match</h2>
        <div className="variants">
          {examples.map((example, index) => (
            <div className="variant" key={index} style={{ cursor: "default" }}>
              <span className="head">
                <span className="angle">example {index + 1}</span>
                <span style={{ flex: 1 }} />
                <button onClick={() => setExamples(examples.filter((_, i) => i !== index))}>✕</button>
              </span>
              <textarea
                value={example}
                onChange={(e) =>
                  setExamples(examples.map((x, i) => (i === index ? e.target.value : x)))
                }
                style={{ minHeight: 130 }}
              />
            </div>
          ))}
        </div>
        <div className="actions">
          <button onClick={() => setExamples([...examples, ""])}>+ Add example</button>
          <span className="note">
            Captions you have actually approved, in your own Thai. These do more than any description.
          </span>
        </div>
      </div>

      <div className="actions">
        <button className="primary" onClick={save} disabled={pending}>
          {pending ? "Saving…" : "Save brief"}
        </button>
        {saved && <span className="note">{saved}</span>}
      </div>

      {errors.length > 0 && (
        <div className="reasons">
          <strong>Not saved</strong>
          <ul>{errors.map((r) => <li key={r}>{r}</li>)}</ul>
        </div>
      )}
    </>
  );
}
