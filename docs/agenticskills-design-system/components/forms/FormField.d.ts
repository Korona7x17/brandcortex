import * as React from 'react';

/** Two-column form row: mono label rail on the left, control on the right. */
export interface FormFieldProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  required?: boolean;
  /** Nano-scale hint under the label, e.g. 'Title case · max 60 char'. */
  help?: string;
  children: React.ReactNode;
}
export function FormField(props: FormFieldProps): JSX.Element;