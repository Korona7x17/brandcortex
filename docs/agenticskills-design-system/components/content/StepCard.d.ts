import * as React from 'react';

/** Numbered explainer cell for 'How it works' style rows. */
export interface StepCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Mono eyebrow, e.g. 'Step 01'. */
  step?: string;
  title: string;
  description?: string;
  /** Ink-filled mono chip pinned to the bottom of the card. */
  command?: string;
  /** A 22px line-glyph SVG, shown in a 56px ink-bordered square. */
  glyph?: React.ReactNode;
}
export function StepCard(props: StepCardProps): JSX.Element;