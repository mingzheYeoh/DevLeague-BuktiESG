import type { Metadata } from "next";
import { PrototypeNotice } from "@/components/prototype-notice";
import "./globals.css";

export const metadata: Metadata = {
  title: "BuktiESG",
  description:
    "First vertical slice: create a Case, upload a questionnaire, review evidence status, create a submission action.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#F7F9FC] font-sans antialiased">
        <PrototypeNotice />
        <div className="mx-auto max-w-5xl px-6 py-8">{children}</div>
      </body>
    </html>
  );
}
