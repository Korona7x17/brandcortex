import * as React from 'react';

export interface TocItem { id: string; label: string }

/** Sticky in-page nav rail. The active item gets a 2px ink left border. */
export interface TableOfContentsProps extends React.HTMLAttributes<HTMLElement> {
  title?: string;
  items: TocItem[];
  activeId?: string;
  onSelect?: (id: string) => void;
}
export function TableOfContents(props: TableOfContentsProps): JSX.Element;