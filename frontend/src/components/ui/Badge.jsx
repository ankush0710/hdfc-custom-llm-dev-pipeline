const variants = {
  success: "border-green-200 bg-green-50 text-green-700",

  warning: "border-yellow-200 bg-yellow-50 text-yellow-700",

  danger: "border-red-200 bg-red-50 text-red-700",

  info: "border-blue-200 bg-blue-50 text-blue-700",

  neutral: "border-slate-200 bg-slate-50 text-slate-600",

  purple: "border-purple-200 bg-purple-50 text-purple-700",
};

export default function Badge({ children, variant = "neutral", icon: Icon }) {
  return (
    <span
      className={`
        inline-flex
        items-center
        gap-1.5
        rounded-full
        border
        px-2.5
        py-1
        text-xs
        font-medium
        ${variants[variant]}
      `}
    >
      {Icon && <Icon size={12} />}
      {children}
    </span>
  );
}
