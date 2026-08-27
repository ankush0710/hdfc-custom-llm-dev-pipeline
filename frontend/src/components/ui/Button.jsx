"use client";

export default function Button({
  icon: Icon,
  children,
  variant = "default",
  className = "",
  ...props
}) {
  const variants = {
    default: "hover:bg-gray-200 hover:text-[#002B55] border border-gray-400",

    primary: "bg-[#002B55] text-white border border-gray-400",
  };

  return (
    <button
      className={`
        w-full text-sm lg:text-md lg:w-auto
        flex items-center justify-center gap-2
        px-3 py-2
        font-semibold
        transition-colors duration-300
        rounded-md
        cursor-pointer
        ${variants[variant]}
        ${className}
      `}
      {...props}
    >
      {Icon && <Icon className="w-5 h-5" />}
      {children}
    </button>
  );
}
