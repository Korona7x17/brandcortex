import * as React from 'react';

export interface TickerItem { v: string; l: string }

/** Black status strip pinned above the navbar. Carries a live pulse dot. */
export interface TickerProps extends React.HTMLAttributes<HTMLDivElement> {
  version?: string;
  date?: string;
  /** Stat pairs shown in the middle. Hidden below 640px. */
  feed?: TickerItem[];
  /** Right-hand hint text. */
  hint?: string;
}
export function Ticker(props: TickerProps): JSX.Element;