export default function Footer() {
  return (
    <div className="w-full py-5 bg-white border-b border-gray-200 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row items-center justify-between px-6">
        <div>
          <p className="text-xs lg:text-[14px] text-gray-400">
            HDFC LLM Forge &copy; {new Date().getFullYear()}. All rights
            reserved.
          </p>
        </div>
        <div>
          <ul className="flex gap-5">
            <li className="text-xs lg:text-[14px] text-gray-400 hover:text-gray-700 cursor-pointer">
              Privacy Policy
            </li>
            <li className="text-xs lg:text-[14px] text-gray-400 hover:text-gray-700 cursor-pointer">
              Terms of Service
            </li>
            <li className="text-xs lg:text-[14px] text-gray-400 hover:text-gray-700 cursor-pointer">
              Security
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
