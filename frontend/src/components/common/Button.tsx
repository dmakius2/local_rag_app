import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  children: ReactNode;
}

export function Button({ variant = "secondary", className = "", children, ...rest }: ButtonProps) {
  return (
    <button className={`btn btn-${variant} ${className}`.trim()} {...rest}>
      {children}
    </button>
  );
}
