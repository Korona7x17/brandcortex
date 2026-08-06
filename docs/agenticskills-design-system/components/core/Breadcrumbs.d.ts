import * as React from 'react';

export interface Crumb { label: string; href?: string }

/** Mono uppercase breadcrumb trail. The last item should omit href. */
export interface BreadcrumbsProps extends React.HTMLAttributes<HTMLElement> {
  items: Crumb[];
}
export function Breadcrumbs(props: BreadcrumbsProps): JSX.Element;