interface LoadingSpinnerProps {
  readonly message?: string;
  readonly size?: number;
}

const LoadingSpinner = ({ message = 'Loading…', size = 40 }: LoadingSpinnerProps) => (
  <div className="flex flex-col items-center justify-center gap-4 p-12" role="status" aria-busy="true">
    <svg
      className="animate-spin"
      width={size}
      height={size}
      viewBox="0 0 50 50"
      aria-hidden="true"
    >
      <circle
        className="stroke-border-dark"
        cx="25"
        cy="25"
        r="20"
        fill="none"
        strokeWidth="4"
      />
      <circle
        className="stroke-primary"
        cx="25"
        cy="25"
        r="20"
        fill="none"
        strokeWidth="4"
        strokeDasharray="80 200"
        strokeLinecap="round"
      />
    </svg>
    {message && <p className="text-text-dim text-sm font-mono">{message}</p>}
  </div>
);

export default LoadingSpinner;
