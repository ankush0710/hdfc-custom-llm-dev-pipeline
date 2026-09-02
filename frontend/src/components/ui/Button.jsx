"use client";

import { Loader2, RefreshCw } from "lucide-react";

export default function Button({
  icon: Icon,
  children,
  variant = "default",
  className = "",
  loading = false,
  ...props
}) {
  const variants = {
    default: "hover:bg-gray-200 hover:text-[#002B55] border border-gray-400",
    primary: "bg-[#002B55] text-white border border-gray-400",
  };

  const isSpinning =
    loading ||
    Icon === Loader2 ||
    Icon?.displayName === "Loader2" ||
    Icon?.name === "Loader2" ||
    (Icon === RefreshCw && (props.disabled || (typeof children === "string" && children.toLowerCase().includes("refreshing")))) ||
    (Icon?.displayName === "RefreshCw" && props.disabled) ||
    (Icon?.name === "RefreshCw" && props.disabled) ||
    (props.disabled && typeof children === "string" && (
      children.toLowerCase().includes("...") ||
      children.toLowerCase().includes("ing")
    ));

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
        ${props.disabled ? "cursor-not-allowed opacity-70" : ""}
        ${variants[variant]}
        ${className}
      `}
      {...props}
    >
      {Icon && (
        <Icon
          className={`w-5 h-5 shrink-0 ${isSpinning ? "animate-spin" : ""}`}
        />
      )}
      {children}
    </button>
  );
}
