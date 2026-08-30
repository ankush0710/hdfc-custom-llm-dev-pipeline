export default function Footer() {
  return (
    <footer className="w-full py-5 bg-white border-t border-gray-200 shadow-sm mt-auto">
      <div className="flex flex-col gap-4 md:flex-row items-center justify-between px-6 max-w-7xl mx-auto">
        <div>
          <p className="text-xs lg:text-sm text-gray-500">
            HDFC LLM Forge &copy; {new Date().getFullYear()}. All rights reserved.
          </p>
        </div>
        <div>
          <ul className="flex gap-5">
            <li className="text-xs lg:text-sm text-gray-500 hover:text-gray-800 cursor-pointer transition-colors">
              Privacy Policy
            </li>
            <li className="text-xs lg:text-sm text-gray-500 hover:text-gray-800 cursor-pointer transition-colors">
              Terms of Service
            </li>
            <li className="text-xs lg:text-sm text-gray-500 hover:text-gray-800 cursor-pointer transition-colors">
              Security
            </li>
          </ul>
        </div>
      </div>
    </footer>
  );
}

