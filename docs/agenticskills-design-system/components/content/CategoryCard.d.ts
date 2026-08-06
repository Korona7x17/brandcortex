import * as React from 'react';

/** Compact category cell for the 4-up browse grid. */
export interface CategoryCardProps extends React.HTMLAttributes<HTMLElement> {
  name: string;
  count?: number;
  description?: string;
  /** Slug list rendered as a mono footer run. */
  topSkills?: string[];
  /** Mono corner index, e.g. 'C01'. */
  index?: string;
  /** A 18px line-glyph SVG. */
  icon?: React.ReactNode;
  href?: string;
}
export function CategoryCard(props: CategoryCardProps): JSX.Element;