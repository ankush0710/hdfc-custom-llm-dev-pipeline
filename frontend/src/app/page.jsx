//=======================================================================================//
/*
The main dashboard that shows the all information aout the deployed models
*/
//=======================================================================================//
"use client";
import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";
import Footer from "@/components/layout/Footer";
import StatCard from "@/components/ui/StatCard";
import ActivityCard from "@/components/ui/ActivityCard";
import ModelsTable from "@/components/tables/ModelsTable";
import Button from "@/components/ui/Button";
import { ChartData } from "@/sampleData/DashboardChartData";
import { DashboardTableData } from "@/sampleData/DashboardTableData";
import LineChart from "@/components/charts/LineChart";
import { useState } from "react";
import { Download, Plus } from "lucide-react";

export default function Dashboard() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <div className="min-h-screen bg-gray-50">
        {/* side bar consists -> all routes section */}
        <Sidebar isOpen={isOpen} onClose={() => setIsOpen(false)} />

        {/* navbar consists -> profile image and search bar section  */}
        <Navbar onMenuClick={() => setIsOpen((prev) => !prev)} />

        <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]">
          {/* Header row containing title and actions section */}
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div className="px-5">
              <h1 className="text-blue-900 font-bold text-3xl">
                LLM Pipeline Overview
              </h1>
              <p className="pt-1 lg:pt-3 text-gray-600">
                System performance and model metrics
              </p>
            </div>
            <div className="flex items-center gap-2 px-5 lg:px-0">
              <Button icon={Download}>Export Report</Button>

              <Button icon={Plus} variant="primary">
                New Pipeline
              </Button>
            </div>
          </div>

          {/* stat cards for displaying all info about trained model section */}
          <div className="my-6 px-5">
            <StatCard />
          </div>

          {/* tarining performance data and recent activity section  */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[3.5fr_1.5fr] my-10 px-5">
            <div className="min-w-0">
              <LineChart
                title="Training Performance"
                data={ChartData}
                xKey="epoch"
                lines={[
                  {
                    dataKey: "trainingLoss",
                    name: "Training Loss",
                    color: "#2563eb",
                  },
                  {
                    dataKey: "validationLoss",
                    name: "Validation Loss",
                    color: "#dc2626",
                  },
                ]}
              />
            </div>
            <div className="min-w-0">
              <ActivityCard />
            </div>
          </div>

          {/* model table section will show the all the information relates to the registered models  */}
          <div className="min-w-0 my-6 px-5">
            <ModelsTable data={DashboardTableData} />
          </div>
        </main>

        {/* Footer here  */}
        <div className="mt-12 lg:ml-[280px]">
          <Footer />
        </div>
      </div>
    </>
  );
}
