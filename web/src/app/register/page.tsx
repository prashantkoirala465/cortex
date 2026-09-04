"use client";

import { useRouter } from "next/navigation";
import { AuthForm } from "@/components/auth-form";
import { useAuth } from "@/context/auth-context";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();

  return (
    <AuthForm
      mode="register"
      onSubmit={async (email, password) => {
        await register(email, password);
        router.push("/");
      }}
    />
  );
}
