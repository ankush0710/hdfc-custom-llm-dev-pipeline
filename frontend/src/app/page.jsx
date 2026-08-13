//=======================================================================================//
/*
The main dashboard that shows the all information aout the deployed models
*/
//=======================================================================================//
"use client"
import Navbar from '@/components/layout/Navbar';
import Sidebar from '@/components/layout/Sidebar';
import StatCard from "@/components/ui/StatCard";
import { ChartData } from '@/sampleData/ChartData';
import LineChart from "@/components/charts/LineChart";
import { useState } from 'react';
import { Download, Plus } from 'lucide-react';

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
              <h1 className="text-blue-900 font-bold text-3xl">LLM Pipeline Overview</h1>
              <p className="pt-1 lg:pt-3 text-gray-600">System performance and model metrics</p>
            </div>
            <div className="flex items-center gap-2 px-5 lg:px-0">
              <button className='w-full lg:w-auto flex items-center justify-center gap-2 px-3 py-2 font-semibold hover:bg-gray-200 hover:text-blue-900 transition-colors duration-300 rounded-md cursor-pointer border border-gray-400 '><Download className='w-5 h-5 mr-2 font-semibold' />Export Report</button>
              <button className='w-full lg:w-auto flex items-center justify-center gap-2 px-3 py-2 font-semibold bg-[#002B55] text-white transition-colors duration-300 rounded-md cursor-pointer border border-gray-400'><Plus className='w-5 h-5 mr-2 font-semibold' />New Pipeline</button>
            </div>
          </div>

          {/* stat cards for displaying all info about trained model section */}
          <div className='my-10 px-5'>
            <StatCard />
          </div>

          {/* tarining performance data and recent activity section  */}
          <div className='my-10 px-5'>
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
              ]} />
          </div>
        </main>
      </div>
    </>
  )
}
