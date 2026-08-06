import * as React from 'react';

/**
 * Inverted code surface for install demos and config samples.
 * Colour inside is carried by className on spans: pr, cmd, ok, dim, k, s, c.
 * @startingPoint section="Code" subtitle="Inverted terminal / config panel" viewport="700x300"
 */
export interface TerminalProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Centre label in the title bar. */
  title?: string;
  /** Right-hand label, e.g. a duration or 'schema'. */
  meta?: React.ReactNode;
  /** Pre-formatted content. Use <span className="cmd|ok|dim|pr|k|s|c"> to tint. */
  children: React.ReactNode;
  dots?: boolean;
  /** Appends the blinking block cursor. */
  cursor?: boolean;
}
export function Terminal(props: TerminalProps): JSX.Element;