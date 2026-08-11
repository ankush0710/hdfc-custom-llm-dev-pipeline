//========================================================================================//
/*
Sidebar consists -> Pipeline Management, Evaluation, Model, Deployment.
*/
//=======================================================================================//
"use client"


import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Database,
    BrainCircuit,
    ChartColumn,
    Box,
    SquareTerminal,
} from "lucide-react";

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
    }

]

const eveluationItems = [
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
        name: "Playground",
        href: "/playground",
        icon: SquareTerminal,
    }
]


//======================= side bar function ==============================================//
function SidebarItem({ item, pathname }) {
    const Icon = item.icon;
    const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

    return (
        <Link href={item.href} className={`relative flex items-center gap-4 px-5 py-4 rounded-r-lg transition-all duration-300 group ${isActive ? " bg-[#07477F] text-white" : "text-white hover:bg-[#063967]"}`}>
            {isActive && (<span className="absolute left-0 top-0 h-full w-1 bg-red-500" />
            )}
            <Icon size={23} strokeWidth={2} className={`shrink-0 ${isActive ? "text-white" : "text-white group-hover:text-white"}`} />
            <span className="text-sm font-medium tracking-wide">
                {item.name}
            </span>
        </Link>
    );
}


//============================ side bar starts from here ==================================//
export default function sidebar() {
    const pathname = usePathname()

    return (
        <div className="fixed left-0 top-0 z-40 h-screen w-[280px] bg-[#002B55]">
            <div className="px-6 pt-8 pb-12">
                <Link href="/" className="flex items-center gap-4">

                    {/* logo  */}
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[#003A70]">
                        <img src="/HDFC_Forge_logo.png" alt="HDFC Forge" className="h-9 w-9 object-contain" />
                    </div>

                    {/* Brand  */}
                    <div>
                        <h1 className="text-[25px] font-bold leading-none tracking-tight text-gray-300">HDFC Bank</h1>
                        <p className="mt-2 text-sm font-medium text-gray-300">AI Enterprise</p>
                    </div>
                </Link>
            </div>

            {/* ============== Navigation ================  */}
            <nav className="px-4">

                {/* pipeline managment routes */}
                <div>
                    <h2 className="mb-4 px-5 text-md font-semibold tracking-wide text-gray-400">PIPELINE MANAGEMENT</h2>

                    {pipelineItems.map((items) => {
                        return (
                            <div key={items.name} className="space-y-2">
                                <SidebarItem key={items.href} item={items} pathname={pathname} />
                            </div>
                        )
                    })}
                </div>

                {/* evaluation and tracking routes  */}
                <div className="mt-8">
                    <h2 className="mb-4 px-5 text-md font-semibold tracking-wide text-gray-400">MODEL EVALUATION</h2>

                    {eveluationItems.map((items) => {
                        return (
                            <div key={items.name} className="space-y-2">
                                <SidebarItem key={items.href} item={items} pathname={pathname} />
                            </div>
                        )
                    })}
                </div>
            </nav>
        </div>
    )
}

