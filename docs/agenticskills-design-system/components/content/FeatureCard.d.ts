import * as React from 'react';

/** Larger editorial card for the Editor's picks row. Belongs in a HairlineGrid variant="ink". */
export interface FeatureCardProps extends React.HTMLAttributes<HTMLElement> {
  name: string;
  author?: string;
  description?: string;
  platforms?: string[];
  installs?: string;
  stars?: string;
  rank?: 'S' | 'A' | 'B' | 'C';
  /** Right-hand qualifier, e.g. 'Official' or 'Verified'. */
  status?: string;
  /** Boxed label top-left. Default 'Featured'. */
  label?: string;
  href?: string;
}
export function FeatureCard(props: FeatureCardProps): JSX.Element;