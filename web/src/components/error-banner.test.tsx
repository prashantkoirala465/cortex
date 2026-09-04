import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ErrorBanner, friendlyErrorMessage } from "@/components/error-banner";
import { ApiError } from "@/lib/api";

describe("friendlyErrorMessage", () => {
  it("gives a network-specific message for a TypeError", () => {
    expect(friendlyErrorMessage(new TypeError("failed to fetch"))).toBe(
      "Can't reach the server. Check that the API is running.",
    );
  });

  it("surfaces an ApiError's message", () => {
    expect(friendlyErrorMessage(new ApiError(404, "note not found"))).toBe("note not found");
  });

  it("falls back to a generic message for unrecognized errors", () => {
    expect(friendlyErrorMessage("plain string")).toBe("Something went wrong.");
  });
});

describe("ErrorBanner", () => {
  it("renders the message", () => {
    render(<ErrorBanner message="oops" />);
    expect(screen.getByText("oops")).toBeInTheDocument();
  });

  it("calls onRetry when the retry button is clicked", () => {
    const onRetry = vi.fn();
    render(<ErrorBanner message="oops" onRetry={onRetry} />);

    fireEvent.click(screen.getByText("Retry"));

    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("does not render a retry button when onRetry is omitted", () => {
    render(<ErrorBanner message="oops" />);
    expect(screen.queryByText("Retry")).not.toBeInTheDocument();
  });
});
