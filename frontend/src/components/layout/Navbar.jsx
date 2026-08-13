//========================================================================================//
/*
Navbar consists -> header, search bar, notification, settings, profile
*/
//=======================================================================================//
"use client"
import Link from "next/link"
import { Menu, Bell, Settings, User, Search, Sparkles } from 'lucide-react';

export default function Navbar({ onMenuClick }) {
    return (
        <nav className="fixed top-0 z-30 w-full bg-white border-b border-gray-200 px-4 py-2 shadow-sm">
            <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 lg:ml-[280px]">
                {/* Left section: Hamburger menu & Bank Logo / Title */}
                <div className="flex items-center gap-3">
                    <button onClick={onMenuClick} className="p-1.5 text-black hover:text-blue-900 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer lg:hidden">
                        <Menu className="w-6 h-6" />
                    </button>
                    <Link href="/" className="flex items-center gap-2 text-[#000000] font-bold text-lg tracking-tight">
                        <img src="/HDFC_Forge_logo.png" alt="logo" className="h-10 lg:h-14 w-auto object-contain" />
                    </Link>
                </div>

                {/* Middle section: Search Bar */}
                <div className="flex-1 max-w-md hidden md:block">
                    <div className="relative">
                        <Search className="w-6 h-6 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search models, datasets, fine-tuning jobs..."
                            className="w-full pl-12 pr-4 py-2.5 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all"
                        />
                    </div>
                </div>

                {/* Right section: Actions & User Profile */}
                <div className="flex items-center gap-3">
                    <button className="p-2 text-black hover:text-blue-900 hover:bg-gray-100 rounded-lg transition-colors relative cursor-pointer" aria-label="Notifications">
                        <Bell className="w-5 h-5 md:h-6 md:w-6" />
                        <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-600 rounded-full"></span>
                    </button>
                    <button className="p-2 text-black hover:text-blue-900 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer" aria-label="Settings">
                        <Settings className="w-5 h-5 md:h-6 md:w-6" />
                    </button>

                    <div className="h-6 w-0.5 bg-gray-400 mx-1"></div>

                    {/* User Profile */}
                    <div className="flex items-center gap-2 cursor-pointer p-1 hover:bg-gray-50 rounded-lg transition-colors">
                        <div className="w-8 h-8 rounded-full bg-blue-900 text-white flex items-center justify-between justify-center font-medium text-xs">
                            <User className="w-4 h-4" />
                        </div>
                        <div className="hidden lg:block text-left text-xs">
                            <p className="font-semibold text-gray-800 leading-tight">Admin User</p>
                            <p className="text-gray-500 text-[10px]">AI Engineer</p>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    );
}