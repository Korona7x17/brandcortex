import * as React from 'react';

export type SegOption = string | { value: string; label: string };

/**
 * Hairline-divided button row. Active segment inverts to ink.
 * Used for filter chips, sort modes, category pickers and install-method tabs.
 * @startingPoint section="Forms" subtitle="Filter chips and mode switches" viewport="700x120"
 */
export interface SegmentedControlProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange'> {
  options: SegOption[];
  value?: string;
  onChange?: (value: string) => void;
}
export function SegmentedControl(props: SegmentedControlProps): JSX.Element;