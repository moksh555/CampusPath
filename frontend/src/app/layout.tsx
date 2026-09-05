import type { ReactNode } from "react";
import "@/styles/globals.css";
export const metadata = {
  title: "CampusPath — Find your own path",
  description: "A personal university research workspace",
};
export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
