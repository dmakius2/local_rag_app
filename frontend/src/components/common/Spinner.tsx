interface SpinnerProps {
  size?: "sm" | "md";
}

export function Spinner({ size = "md" }: SpinnerProps) {
  return <span className={`spinner spinner-${size}`} role="status" aria-label="Loading" />;
}
