import * as React from 'react';

/**
 * Standard page opener: breadcrumbs, eyebrow, display title, lede.
 * @startingPoint section="Layout" subtitle="Page opener with breadcrumb and lede" viewport="700x300"
 */
export interface PageHeadProps extends React.HTMLAttributes<HTMLElement> {
  /** Pass a <Breadcrumbs /> element. */
  crumbs?: React.ReactNode;
  eyebrow?: string;
  /** Wrap one accent word in <em>. */
  title: React.ReactNode;
  lede?: React.ReactNode;
  /** Extra content below the lede, e.g. a <StatRow />. */
  children?: React.ReactNode;
}
export function PageHead(props: PageHeadProps): JSX.Element;