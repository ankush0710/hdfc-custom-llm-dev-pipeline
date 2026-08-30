"use client";

import { useState } from "react";
import { Merriweather } from "next/font/google";
import { usePathname } from "next/navigation";
import { Toaster } from "sonner";
import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";
import Footer from "@/components/layout/Footer";
import { AuthProvider } from "@/app/context/AuthContext";
import "./globals.css";

const merriweather = Merriweather({
  subsets: ["latin"],
  variable: "--font-merriweather",
  weight: ["300", "400", "700", "900"],
});

function AppLayout({ children }) {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();
  const isAuthPage = pathname === "/login" || pathname === "/signup";

  if (isAuthPage) {
    return <main className="min-h-screen w-full">{children}</main>;
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Sidebar isOpen={isOpen} onClose={() => setIsOpen(false)} />
      <Navbar onMenuClick={() => setIsOpen((prev) => !prev)} />
      <div className="flex-1 flex flex-col">
        {children}
      </div>
      <div className="mt-auto lg:ml-[280px]">
        <Footer />
      </div>
    </div>
  );
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${merriweather.variable} font-merriweather min-h-screen flex flex-col`}>
        <AuthProvider>
          <AppLayout>{children}</AppLayout>
          <Toaster position="top-right" richColors closeButton />
        </AuthProvider>
      </body>
    </html>
  );
}

