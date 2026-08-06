import * as React from 'react';

/**
 * The core layout device: a zero-gap grid where separation is drawn by borders.
 * The wrapper draws top+left; each child draws right+bottom.
 * @startingPoint section="Layout" subtitle="Zero-gap bordered grid" viewport="700x260"
 */
export interface HairlineGridProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Column count, or a raw grid-template-columns string. Default 3. */
  columns?: number | string;
  /** 'hairline' = grey rules all round. 'ink' = single row banded by black rules. */
  variant?: 'hairline' | 'ink';
  children: React.ReactNode;
}
export function HairlineGrid(props: HairlineGridProps): JSX.Element;