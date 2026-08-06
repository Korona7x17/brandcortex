import * as React from 'react';

/** Library article card: 5:3 image band over a padded body. */
export interface ArticleCardProps extends React.HTMLAttributes<HTMLElement> {
  title: string;
  excerpt?: string;
  category?: string;
  /** e.g. '14 min'. The word 'read' is appended. */
  readTime?: string;
  date?: string;
  /** Real imagery. Omit to fall back to the diagonal-stripe placeholder. */
  image?: React.ReactNode;
  href?: string;
  action?: string;
}
export function ArticleCard(props: ArticleCardProps): JSX.Element;