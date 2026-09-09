import { Merriweather } from "next/font/google";
import AppShell from "@/components/layout/AppShell";
import "./globals.css";

const merriweather = Merriweather({
  subsets: ["latin"],
  variable: "--font-merriweather",
  weight: ["300", "400", "700", "900"],
});

export const metadata = {
  title: "HDFC Custom LLM Pipeline",
  description: "Enterprise LLM development pipeline for HDFC",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${merriweather.variable} font-merriweather min-h-screen flex flex-col`}>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
