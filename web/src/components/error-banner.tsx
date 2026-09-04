export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded border border-red-600/30 bg-red-600/5 px-3 py-2 text-sm text-red-600 dark:border-red-400/30 dark:text-red-400">
      <span>{message}</span>
      {onRetry && (
        <button onClick={onRetry} className="shrink-0 underline">
          Retry
        </button>
      )}
    </div>
  );
}

export function friendlyErrorMessage(err: unknown): string {
  if (err instanceof TypeError) {
    return "Can't reach the server. Check that the API is running.";
  }
  if (err && typeof err === "object" && "message" in err && typeof err.message === "string") {
    return err.message;
  }
  return "Something went wrong.";
}
