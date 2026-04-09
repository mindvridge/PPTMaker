import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DeckCraft - AI PPT Generator",
  description: "AI가 디자인 품질 높은 PPT를 자동 생성합니다",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
