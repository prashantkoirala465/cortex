"use client";

import { useRouter } from "next/navigation";
import { AuthForm } from "@/components/auth-form";
import { useAuth } from "@/context/auth-context";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();

  return (
    <AuthForm
      mode="login"
      onSubmit={async (email, password) => {
        await login(email, password);
        router.push("/");
      }}
    />
  );
}
