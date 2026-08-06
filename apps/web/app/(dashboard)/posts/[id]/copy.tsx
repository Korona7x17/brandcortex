"use client";

import { useState } from "react";

/**
 * Copy to clipboard.
 *
 * Load-bearing until publishing works: the first comment has to be pasted into the channel by hand,
 * and it carries the UTM campaign. Retyping it silently breaks attribution for that post, which is
 * the kind of failure nobody notices because the post looks fine.
 */
export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  return (
    <button
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
        } catch {
          // Clipboard access needs a secure context; select the text instead of failing silently.
          const area = document.createElement("textarea");
          area.value = text;
          document.body.appendChild(area);
          area.select();
          document.execCommand("copy");
          area.remove();
        }
        setCopied(true);
        setTimeout(() => setCopied(false), 1600);
      }}
      style={{ fontSize: 12, padding: "4px 10px" }}
    >
      {copied ? "Copied" : label}
    </button>
  );
}
