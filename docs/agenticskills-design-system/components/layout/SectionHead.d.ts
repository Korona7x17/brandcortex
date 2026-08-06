import * as React from 'react';

/** Numbered section header: eyebrow index, title with serif accent, optional desc or CTA. */
export interface SectionHeadProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Mono eyebrow, e.g. '03 · Index'. */
  index?: string;
  /** Wrap one accent word in <em> to pick up the serif italic. */
  title: React.ReactNode;
  desc?: React.ReactNode;
  cta?: string;
  ctaHref?: string;
}
export function SectionHead(props: SectionHeadProps): JSX.Element;