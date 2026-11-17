import type { ButtonHTMLAttributes } from 'react';
import { Link } from 'react-router';

type ButtonVariant = 'primary' | 'secondary' | 'tertiary';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  /* With a target URL the button goes to another page, so it renders a link. */
  to?: string;
}

// inline-block lets the vertical padding of a link take up space, as on a <button>
const BASE_STYLE =
  'inline-block rounded-xl px-6 py-2 text-xl font-medium uppercase';

const BUTTON_STYLE: Record<ButtonVariant, string> = {
  primary: 'bg-hazelnut-light hover:bg-hazelnut-dark',
  secondary:
    'border-2 border-dark-espresso bg-burlap-tan hover:bg-hazelnut-dark',
  tertiary: 'border border-black hover:bg-white',
};

export default function Button({
  variant = 'primary',
  to,
  children,
  ...buttonProps
}: ButtonProps) {
  const className = `${BASE_STYLE} ${BUTTON_STYLE[variant]}`;

  if (to !== undefined) {
    return (
      <Link to={to} className={className}>
        {children}
      </Link>
    );
  }

  return (
    <button className={className} {...buttonProps}>
      {children}
    </button>
  );
}
