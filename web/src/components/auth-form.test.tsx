import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AuthForm } from "@/components/auth-form";
import { ApiError } from "@/lib/api";

describe("AuthForm", () => {
  it("renders login mode with a link to register", () => {
    render(<AuthForm mode="login" onSubmit={vi.fn()} />);
    expect(screen.getByRole("heading", { name: "Log in" })).toBeInTheDocument();
    expect(screen.getByText("Sign up")).toBeInTheDocument();
  });

  it("renders register mode with a link to login", () => {
    render(<AuthForm mode="register" onSubmit={vi.fn()} />);
    expect(screen.getByRole("heading", { name: "Create an account" })).toBeInTheDocument();
    expect(screen.getByText("Log in")).toBeInTheDocument();
  });

  it("calls onSubmit with the entered email and password", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<AuthForm mode="login" onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "a@b.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: "Log in" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith("a@b.com", "password123"));
  });

  it("shows the api error's message when onSubmit rejects", async () => {
    const onSubmit = vi.fn().mockRejectedValue(new ApiError(401, "invalid email or password"));
    render(<AuthForm mode="login" onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "a@b.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrongpassword" } });
    fireEvent.click(screen.getByRole("button", { name: "Log in" }));

    await waitFor(() =>
      expect(screen.getByText("invalid email or password")).toBeInTheDocument(),
    );
  });
});
