/**
 * Word-level diff between what the engine wrote and what the reviewer is about to approve.
 *
 * This is the display side of the most valuable signal the system produces: an edit is a direct
 * statement about where the generation engine is off. The API stores both texts rather than a diff,
 * so the comparison stays recomputable — this is one way of reading it, not the record.
 *
 * Thai is written without spaces between words, so splitting on whitespace gives long "words" and a
 * coarse diff. That is the honest failure mode: it marks a whole phrase as changed rather than
 * inventing a segmentation the language does not have. Proper Thai segmentation needs a dictionary,
 * which is a real dependency for a cosmetic gain.
 */

export type Chunk = { value: string; kind: "same" | "added" | "removed" };

const tokenize = (text: string): string[] => text.split(/(\s+)/).filter(Boolean);

export function diffWords(before: string, after: string): Chunk[] {
  const a = tokenize(before);
  const b = tokenize(after);

  // Longest common subsequence table. Captions are a few dozen tokens; the quadratic cost is
  // irrelevant at that size and the alternative is a dependency.
  const lcs: number[][] = Array.from({ length: a.length + 1 }, () =>
    new Array<number>(b.length + 1).fill(0),
  );
  for (let i = a.length - 1; i >= 0; i--) {
    for (let j = b.length - 1; j >= 0; j--) {
      lcs[i][j] = a[i] === b[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
    }
  }

  const chunks: Chunk[] = [];
  const push = (value: string, kind: Chunk["kind"]) => {
    const last = chunks[chunks.length - 1];
    if (last && last.kind === kind) last.value += value;
    else chunks.push({ value, kind });
  };

  let i = 0;
  let j = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) push(a[i++], "same"), j++;
    else if (lcs[i + 1][j] >= lcs[i][j + 1]) push(a[i++], "removed");
    else push(b[j++], "added");
  }
  while (i < a.length) push(a[i++], "removed");
  while (j < b.length) push(b[j++], "added");

  return chunks;
}
