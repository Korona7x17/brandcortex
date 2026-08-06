import * as React from 'react';

export interface NavLink { id: string; label: string; href: string }

/**
 * Sticky hairline header with brand lockup, links, search trigger and CTA.
 * @startingPoint section="Navigation" subtitle="Sticky header with search and CTA" viewport="700x120"
 */
export interface NavbarProps extends React.HTMLAttributes<HTMLElement> {
  /** id of the active link — underlines it in ink. */
  active?: string;
  links?: NavLink[];
  /** Wordmark text. Rendered as plain type; the system has no logo asset. */
  brand?: string;
  search?: boolean;
  searchLabel?: string;
  cta?: string;
  ctaHref?: string;
}
export function Navbar(props: NavbarProps): JSX.Element;