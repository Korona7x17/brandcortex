import * as React from 'react';

export interface FooterLink { label: string; href: string }
export interface FooterColumn { title: string; links: FooterLink[] }

/** Four-column footer on paper, closed by a hairline meta row. */
export interface FooterProps extends React.HTMLAttributes<HTMLElement> {
  brand?: string;
  blurb?: string;
  columns?: FooterColumn[];
  /** Bottom-left meta, e.g. copyright. */
  left?: React.ReactNode;
  /** Bottom-right meta, e.g. build version. */
  right?: React.ReactNode;
}
export function Footer(props: FooterProps): JSX.Element;