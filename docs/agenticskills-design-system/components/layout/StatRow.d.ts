import * as React from 'react';

export interface Stat { v: React.ReactNode; l: string }

/** Row of mono numerals with uppercase captions, divided by a hairline. */
export interface StatRowProps extends React.HTMLAttributes<HTMLDivElement> {
  items: Stat[];
  /** 'default' on paper · 'inverse' inside a black section (larger numerals, dark rules). */
  variant?: 'default' | 'inverse';
  /** Override the column count — defaults to items.length. */
  columns?: number;
}
export function StatRow(props: StatRowProps): JSX.Element;