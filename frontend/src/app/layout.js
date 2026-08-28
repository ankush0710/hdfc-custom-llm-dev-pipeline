"use client";

import { useState } from "react";
import { Merriweather } from "next/font/google";
import { Toaster } from "sonner";
import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";
import { AuthProvider } from "@/app/context/AuthContext";
import "./globals.css";

const merriweather = Merriweather({
  subsets: ["latin"],
  variable: "--font-merriweather",
  weight: ["300", "400", "700", "900"],
});

export default function RootLayout({ children }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <html lang="en">
      <body className={`${merriweather.variable} font-merriweather min-h-full flex flex-col`}>
        <AuthProvider>
          <div className="min-h-screen bg-gray-50">
            <Sidebar isOpen={isOpen} onClose={() => setIsOpen(false)} />
            <Navbar onMenuClick={() => setIsOpen((prev) => !prev)} />
            {children}
            <Toaster position="top-right" richColors closeButton />
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
