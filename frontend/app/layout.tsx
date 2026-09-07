import type { Metadata } from "next";
import { fontVariables } from "@/lib/fonts";
import "./globals.css";

export const metadata: Metadata = {
  title: "SIGNAL",
  description:
    "Early language-development screening for children in institutional care. Synthetic-data-only build.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${fontVariables} h-full antialiased`}>
      {/*
        suppressHydrationWarning is scoped to <body> and only to <body>.

        Browser extensions inject attributes here before React hydrates —
        ColorZilla adds `cz-shortcut-listen`, password managers and grammar
        tools add their own — and React then reports a hydration mismatch for
        markup this app never rendered. The warning is real but the cause is
        outside the application, and it is unfixable from inside it.

        The cost is honest: genuine hydration mismatches on this ONE element
        stop being reported. That is why it is not on <html> and not on any
        component that renders real content — a mismatch inside the app still
        fails loudly, which is the warning that actually matters.
      */}
      <body className="min-h-full flex flex-col" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
