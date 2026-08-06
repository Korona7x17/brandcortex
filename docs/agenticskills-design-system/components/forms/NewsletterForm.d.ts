import * as React from 'react';

/**
 * Full-bleed black subscribe band. The page's final emphasis before the footer.
 * @startingPoint section="Forms" subtitle="Inverted subscribe band" viewport="700x340"
 */
export interface NewsletterFormProps extends React.HTMLAttributes<HTMLElement> {
  /** Wrap one accent word in <em> for the serif italic. */
  title: React.ReactNode;
  body?: string;
  placeholder?: string;
  action?: string;
  /** Mono fine print under the form. */
  fine?: string;
  onSubmit?: (e: React.FormEvent) => void;
}
export function NewsletterForm(props: NewsletterFormProps): JSX.Element;