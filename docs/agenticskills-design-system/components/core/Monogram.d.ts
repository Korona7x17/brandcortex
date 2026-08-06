import * as React from 'react';

/** Ink-bordered square holding 1-2 letters. Stands in for platform/product logos. */
export interface MonogramProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Source name — initials are derived from its words. */
  name?: string;
  /** Square edge in px. 36 in dense grids, 42 on featured cards. Default 42. */
  size?: number;
  /** Explicit letters, overriding the derived initials. */
  children?: React.ReactNode;
}
export function Monogram(props: MonogramProps): JSX.Element;