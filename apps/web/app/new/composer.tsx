"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState, useTransition } from "react";

import {
  ApiError,
  type Brand,
  type Subject,
  brandApi,
  previewUrl,
} from "@/lib/api";

/**
 * Make a card the brand has not made yet.
 *
 * The point of this screen is that BrandCortex decides *what* gets drawn. It never draws: the
 * preview is the brand's own live render, and on Draft the API resolves the card's numbers from the
 * brand and captures the PNG — the same builders the render engine uses, so the caption's figures
 * cannot disagree with the image's.
 *
 * Everything specific to a brand comes from `brand.source_types`, so this component has no idea what
 * a swimmer or a stroke is.
 */
export function Composer({ brand }: { brand: Brand }) {
  const router = useRouter();
  const [kind, setKind] = useState(brand.source_types[0]?.key ?? "");
  const sourceType = brand.source_types.find((t) => t.key === kind);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Subject[]>([]);
  const [picked, setPicked] = useState<Subject | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [reasons, setReasons] = useState<string[]>([]);
  const [searching, setSearching] = useState(false);
  const [drafting, startDraft] = useTransition();

  // Defaults for a form-shaped kind, so the preview has something to render immediately.
  useEffect(() => {
    if (!sourceType) return;
    setFields(Object.fromEntries(sourceType.fields.map((f) => [f.name, f.options[0] ?? ""])));
    setPicked(null);
    setResults([]);
    setQuery("");
    setReasons([]);
  }, [kind, sourceType]);

  // Debounced, because it hits the brand's search endpoint on every keystroke otherwise.
  useEffect(() => {
    if (!sourceType?.searchable || query.trim().length < 2) {
      setResults([]);
      return;
    }
    let live = true;
    setSearching(true);
    const timer = setTimeout(async () => {
      try {
        const found = await brandApi.search(brand.brand, query.trim());
        if (live) setResults(found);
      } catch {
        if (live) setResults([]);
      } finally {
        if (live) setSearching(false);
      }
    }, 250);
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [query, brand.brand, sourceType?.searchable]);

  const params = useMemo(
    () => (sourceType?.searchable ? (picked?.params ?? null) : fields),
    [sourceType?.searchable, picked, fields],
  );
  const ready = Boolean(params && (sourceType?.searchable ? picked : true));
  const preview = ready && params ? previewUrl(brand, kind, params as Record<string, string>) : null;

  const draft = () =>
    startDraft(async () => {
      setReasons([]);
      try {
        const post = await brandApi.compose({ brand: brand.brand, source_type: kind, params: params! });
        router.push(`/posts/${post.id}`);
      } catch (error) {
        setReasons(error instanceof ApiError ? error.reasons : [(error as Error).message]);
      }
    });

  return (
    <div className="compose">
      <div>
        <div className="kinds">
          {brand.source_types.map((type) => (
            <button key={type.key} data-on={type.key === kind} onClick={() => setKind(type.key)}>
              {type.label}
            </button>
          ))}
        </div>

        <div className="panel">
          {sourceType?.searchable ? (
            <>
              <div className="field">
                <label htmlFor="q">{sourceType.search_hint ?? "Search"}</label>
                <input
                  id="q"
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="ริน…"
                  autoComplete="off"
                />
              </div>

              {searching && <p className="note">searching…</p>}

              <div className="results">
                {results.map((subject) => (
                  <button
                    key={subject.key}
                    className="result"
                    data-on={picked?.key === subject.key}
                    onClick={() => setPicked(subject)}
                  >
                    <span className="name">{subject.label}</span>
                    {subject.sublabel && <span className="sub">{subject.sublabel}</span>}
                    {subject.hint && <span className="hint">{subject.hint}</span>}
                  </button>
                ))}
                {!searching && query.trim().length >= 2 && results.length === 0 && (
                  <p className="note">Nothing found.</p>
                )}
              </div>
            </>
          ) : (
            <div className="field-grid">
              {sourceType?.fields.map((field) => (
                <div className="field" key={field.name}>
                  <label htmlFor={field.name}>{field.label}</label>
                  <select
                    id={field.name}
                    value={fields[field.name] ?? ""}
                    onChange={(e) => setFields({ ...fields, [field.name]: e.target.value })}
                  >
                    {field.options.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          )}

          <div className="actions">
            <button className="primary" onClick={draft} disabled={!ready || drafting}>
              {drafting ? "Drafting…" : "Draft this card"}
            </button>
            <span className="note">
              Captures the image and writes the caption from the card’s own numbers.
            </span>
          </div>

          {reasons.length > 0 && (
            <div className="reasons">
              <strong>Could not draft</strong>
              <ul>
                {reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      <div className="panel preview">
        <h2>Live preview</h2>
        {preview ? (
          // The brand's render, refreshed as you choose. What publishes is the copy captured at
          // draft time, not this.
          // eslint-disable-next-line @next/next/no-img-element
          <img src={preview} alt="card preview" />
        ) : (
          <div className="placeholder">
            {sourceType?.searchable ? "Pick someone to see their card." : "Choose a bucket."}
          </div>
        )}
        <p className="note">
          Rendered by {brand.display_name}. BrandCortex decides what gets drawn; it never draws.
        </p>
      </div>
    </div>
  );
}
