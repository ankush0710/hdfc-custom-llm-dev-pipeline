//=======================================================================================//
/*
The dataset page that shows the all information aout the datasets
*/
//=======================================================================================//
//=======================================================================================//
/*
The main dashboard that shows the all information aout the deployed models
*/
//=======================================================================================//
"use client";
import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";
import Footer from "@/components/layout/Footer";
import Button from "@/components/ui/Button";
import { useState } from "react";
import { Upload } from "lucide-react";

export default function Dashboard() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <div className="min-h-screen bg-gray-50">
        {/* side bar consists -> all routes section */}
        <Sidebar isOpen={isOpen} onClose={() => setIsOpen(false)} />

        {/* navbar consists -> profile image and search bar section  */}
        <Navbar onMenuClick={() => setIsOpen((prev) => !prev)} />

        <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]"></main>

        {/* Footer here  */}
        <div className="mt-12 lg:ml-[280px]">
          <Footer />
        </div>
      </div>
    </>
  );
}
