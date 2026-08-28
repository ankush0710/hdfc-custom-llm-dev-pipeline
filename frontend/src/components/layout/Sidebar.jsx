"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Database,
  BrainCircuit,
  ChartColumn,
  Box,
  Rocket,
  SquareTerminal,
  X,
  LogOut,
  User,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";

const pipelineItems = [
  {
    name: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    name: "Dataset",
    href: "/dataset",
    icon: Database,
  },
  {
    name: "Training",
    href: "/training",
    icon: BrainCircuit,
  },
];

const evaluationItems = [
  {
    name: "Evaluation",
    href: "/evaluation",
    icon: ChartColumn,
  },
  {
    name: "Model",
    href: "/model",
    icon: Box,
  },
  {
    name: "Deployment",
    href: "/deployment",
    icon: Rocket,
  },
  {
    name: "Playground",
    href: "/playground",
    icon: SquareTerminal,
  },
];

const adminItems = [
  {
    name: "User Management",
    href: "/admin/users",
    icon: Users,
  },
];

function SidebarItem({ item, pathname }) {
  const Icon = item.icon;
  const isActive = item.href === "/" ? pathname === "/" : pathname === item.href || pathname.startsWith(`${item.href}/`);

  return (
    <Link
      href={item.href}
      className={`relative flex items-center gap-4 px-5 py-3 rounded-r-lg transition-all duration-300 group ${
        isActive ? " bg-[#07477F] text-white font-bold" : "text-gray-200 hover:bg-[#063967]"
      }`}
    >
      {isActive && <span className="absolute left-0 top-0 h-full w-1 bg-red-500" />}
      <Icon size={20} strokeWidth={2} className="shrink-0 text-white" />
      <span className="text-sm tracking-wide">{item.name}</span>
    </Link>
  );
}

export default function Sidebar({ isOpen, onClose }) {
  const pathname = usePathname();
  const { user, logout, role } = useAuth();

  // Hide sidebar on auth pages
  if (pathname === "/login" || pathname === "/signup") {
    return null;
  }

  const roleColorClass =
    role === "ADMIN"
      ? "bg-red-500/20 text-red-300 border-red-400/40"
      : role === "DS" || role === "DATA_SCIENTIST"
      ? "bg-purple-500/20 text-purple-300 border-purple-400/40"
      : role === "REVIEWER"
      ? "bg-amber-500/20 text-amber-300 border-amber-400/40"
      : "bg-blue-500/20 text-blue-300 border-blue-400/40";

  return (
    <>
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
        />
      )}
      <div
        className={`fixed left-0 top-0 z-40 h-screen w-[280px] bg-[#002B55] transition-transform duration-300 ease-in-out flex flex-col justify-between ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0 lg:z-40`}
      >
        <div className="overflow-y-auto max-h-[calc(100vh-100px)]">
          <button
            onClick={onClose}
            className="absolute right-4 top-4 text-white lg:hidden"
          >
            <X size={24} />
          </button>
          <div className="px-6 pt-6 pb-6 border-b border-blue-900/60">
            <Link href="/" className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#003A70]">
                <img
                  src="/HDFC_Forge_logo.png"
                  alt="HDFC Forge"
                  className="h-9 w-9 object-contain"
                />
              </div>
              <div>
                <h1 className="text-xl font-bold leading-none tracking-tight text-white">
                  HDFC Bank
                </h1>
                <p className="mt-1 text-xs font-medium text-blue-200">
                  AI Enterprise Pipeline
                </p>
              </div>
            </Link>
          </div>

          {/* Navigation Items */}
          <nav className="px-3 pt-6 space-y-6">
            <div>
              <h2 className="mb-2 px-4 text-xs font-bold tracking-wider text-blue-300/80 uppercase">
                Pipeline Management
              </h2>
              {pipelineItems.map((item) => (
                <SidebarItem key={item.href} item={item} pathname={pathname} />
              ))}
            </div>

            <div>
              <h2 className="mb-2 px-4 text-xs font-bold tracking-wider text-blue-300/80 uppercase">
                Model Evaluation
              </h2>
              {evaluationItems.map((item) => (
                <SidebarItem key={item.href} item={item} pathname={pathname} />
              ))}
            </div>

            {/* Admin-Only Management Section */}
            {role === "ADMIN" && (
              <div>
                <h2 className="mb-2 px-4 text-xs font-bold tracking-wider text-amber-300/90 uppercase flex items-center gap-1.5">
                  <ShieldCheck size={13} className="text-amber-400" />
                  <span>Admin & Governance</span>
                </h2>
                {adminItems.map((item) => (
                  <SidebarItem key={item.href} item={item} pathname={pathname} />
                ))}
              </div>
            )}
          </nav>
        </div>

        {/* User Profile & Logout Section at Bottom */}
        <div className="p-4 border-t border-blue-900/60 bg-[#002244]">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white font-bold text-sm">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : "U"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold text-white truncate">
                {user?.full_name || "Enterprise User"}
              </p>
              <p className="text-[11px] text-blue-300 truncate">
                {user?.email || "user@hdfc.com"}
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between gap-2">
            <span
              className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-mono font-bold border ${roleColorClass}`}
            >
              <ShieldCheck size={11} />
              <span>{role}</span>
            </span>

            <button
              onClick={logout}
              className="inline-flex items-center gap-1 text-xs font-medium text-red-300 hover:text-red-100 transition px-2 py-1 rounded hover:bg-red-500/20"
            >
              <LogOut size={13} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
