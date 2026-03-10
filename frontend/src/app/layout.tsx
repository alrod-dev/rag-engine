import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RAG Engine - Document Intelligence",
  description: "Retrieval-Augmented Generation system for intelligent document analysis",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0066cc" />
      </head>
      <body className="bg-gray-50">{children}</body>
    </html>
  );
}
