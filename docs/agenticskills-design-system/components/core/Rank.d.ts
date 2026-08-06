import * as React from 'react';

/** Quality-rank pill. S inverts to an ink fill; A/B/C stay hairline. */
export interface RankProps extends React.HTMLAttributes<HTMLSpanElement> {
  rank: 'S' | 'A' | 'B' | 'C';
  /** Text appended after the letter. Default '-rank'. Pass '' for the bare letter. */
  suffix?: string;
}
export function Rank(props: RankProps): JSX.Element;