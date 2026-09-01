"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Bell, Settings, User, Search, ShieldCheck } from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";

export default function Navbar({ onMenuClick }) {
  const pathname = usePathname();
  const { user, role } = useAuth();

  // Hide Navbar on auth pages
  if (pathname === "/login" || pathname === "/signup") {
    return null;
  }

  const roleColorClass =
    role === "ADMIN"
      ? "bg-red-100 text-red-700 border-red-200"
      : role === "DS" || role === "DATA_SCIENTIST"
        ? "bg-purple-100 text-purple-700 border-purple-200"
        : role === "REVIEWER"
          ? "bg-amber-100 text-amber-700 border-amber-200"
          : "bg-blue-100 text-blue-700 border-blue-200";

  return (
    <nav className="fixed top-0 z-30 w-full bg-white border-b border-gray-200 px-4 py-2 shadow-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 lg:ml-[280px]">
        {/* Left section: Hamburger menu & Bank Logo / Title */}
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuClick}
            className="p-1.5 text-black hover:text-blue-900 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer lg:hidden"
          >
            <Menu className="w-6 h-6" />
          </button>
          <Link
            href="/"
            className="flex items-center gap-2 text-[#000000] font-bold text-lg tracking-tight"
          >
            <img
              src="./images/HDFC_Forge_logo.png"
              alt="logo"
              className="h-10 lg:h-12 w-auto object-contain"
            />
          </Link>
        </div>

        {/* Middle section: Search Bar */}
        <div className="flex-1 max-w-md hidden md:block">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search models, datasets, fine-tuning jobs..."
              className="w-full pl-10 pr-4 py-2 text-xs bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
            />
          </div>
        </div>

        {/* Right section: Actions & Real User Profile */}
        <div className="flex items-center gap-3">
          <button
            className="p-2 text-black hover:text-blue-900 hover:bg-gray-100 rounded-lg transition-colors relative cursor-pointer"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-600 rounded-full"></span>
          </button>
          <button
            className="p-2 text-black hover:text-blue-900 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
            aria-label="Settings"
          >
            <Settings className="w-5 h-5" />
          </button>

          <div className="h-6 w-0.5 bg-gray-300 mx-1"></div>

          {/* User Profile Info */}
          <div className="flex items-center gap-2.5 p-1">
            <div className="w-8 h-8 rounded-full bg-[#002B55] text-white flex items-center justify-center font-bold text-xs">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : "U"}
            </div>
            <div className="hidden lg:block text-left text-xs">
              <p className="font-bold text-gray-900 leading-tight">
                {user?.full_name || "Enterprise User"}
              </p>
              <div className="flex items-center gap-1 mt-0.5">
                <span
                  className={`inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-mono font-bold border ${roleColorClass}`}
                >
                  <ShieldCheck size={10} />
                  <span>{role}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}