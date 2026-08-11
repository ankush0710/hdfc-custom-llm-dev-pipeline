//=======================================================================================//
/*
The Model page that shows the all information about the Model card
*/
//=======================================================================================//
import Navbar from '@/components/layout/Navbar';
import Sidebar from '@/components/layout/Sidebar';
export default function Model() {
    return (
        <>
            <div className="min-h-screen bg-gray-50">
                <Sidebar />
                {/* navbar here  */}
                <div className='ml-[280px]'>
                    <Navbar />

                    <main>
                        <div className="mx-auto text-center mt-10">
                            <h1 className="text-blue-900 font-bold text-3xl"> HDFC Bank- custom LLM development pipeline</h1>
                            <p className="text-black font-bold text-xl">
                                This is Model page
                            </p>
                        </div>
                    </main>
                </div>
            </div>

        </>
    )
}
