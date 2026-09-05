import type { ReactNode } from "react";

/** Bare centered shell shared by sign-in and sign-up. */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return <main className="flex min-h-screen items-center justify-center">{children}</main>;
}
