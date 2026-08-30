"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Lock, User, Eye, EyeOff, Loader2 } from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";
import { getApiErrorMessage } from "@/app/services/apiClient";
import { toast } from "sonner";

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, loading: authLoading } = useAuth();

  const [formData, setFormData] = useState({ email: "", password: "", rememberMe: false });
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.replace("/");
    }
  }, [authLoading, isAuthenticated, router]);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setError("");

    const emailClean = formData.email.trim();
    const passwordClean = formData.password;

    if (!emailClean || !passwordClean) {
      setError("Please enter both username/email and password.");
      return;
    }

    try {
      setSubmitting(true);
      const user = await login(emailClean, passwordClean);
      toast.success("Welcome back!", {
        description: `Logged in as ${user.full_name} (${user.role}).`,
      });
    } catch (err) {
      console.error("Login error:", err);
      const msg = getApiErrorMessage(err, "Invalid email or password.");
      setError(msg);
      toast.error("Login Failed", { description: msg });
    } finally {
      setSubmitting(false);
    }
  };

  const handleForgotPassword = (e) => {
    e.preventDefault();
    toast.info("Password Reset", {
      description: "Please contact your system administrator at admin@hdfc.com to reset credentials.",
    });
  };

  if (authLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#070D1E]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#0a0f1d] p-4 sm:p-6 lg:p-8 relative overflow-hidden">
      {/* Background Dot Grid */}
      <div
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage: "radial-gradient(#64748b 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      {/* Main Split Card */}
      <div className="w-full max-w-4xl lg:max-w-[960px] bg-white rounded-2xl sm:rounded-3xl shadow-2xl overflow-hidden grid grid-cols-1 md:grid-cols-2 relative z-10 border border-slate-800/40">
        
        {/* Left Side: Form */}
        <div className="p-8 sm:p-10 lg:p-12 flex flex-col justify-between bg-white text-slate-800 min-h-[500px]">
          <div>
            {/* Logo and Brand */}
            <div className="flex items-center gap-2.5 mb-8">
              <div className="h-8 w-8 rounded-lg bg-[#002B55] flex items-center justify-center overflow-hidden p-1 shadow-sm">
                <img
                  src="/Images/HDFC_Forge_logo.png"
                  alt="HDFC LLM Forge"
                  className="h-full w-full object-contain"
                />
              </div>
              <span className="text-sm font-bold tracking-tight text-[#002B55]">
                HDFC LLM Forge
              </span>
            </div>

            {/* Header */}
            <div className="mb-6">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Welcome Back
              </h1>
              <p className="text-xs sm:text-sm text-slate-500 mt-1 font-normal">
                Sign in to access the Enterprise Pipeline.
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-5 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700 font-medium animate-fadeIn">
                {error}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Username / Email */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Username / Email
                </label>
                <div className="relative flex items-center">
                  <User
                    className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                    size={16}
                  />
                  <input
                    type="text"
                    required
                    placeholder="enter your username"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-slate-700">
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={handleForgotPassword}
                    className="text-[11px] font-medium text-slate-500 hover:text-[#002B55] hover:underline transition cursor-pointer"
                  >
                    Forgot Password?
                  </button>
                </div>
                <div className="relative flex items-center">
                  <Lock
                    className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                    size={16}
                  />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full pl-10 pr-10 py-2.5 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition cursor-pointer"
                  >
                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              {/* Remember Me */}
              <div className="flex items-center gap-2 pt-0.5">
                <input
                  type="checkbox"
                  id="rememberMe"
                  checked={formData.rememberMe}
                  onChange={(e) => setFormData({ ...formData, rememberMe: e.target.checked })}
                  className="h-3.5 w-3.5 rounded border-slate-300 text-[#002B55] focus:ring-[#002B55] cursor-pointer"
                />
                <label
                  htmlFor="rememberMe"
                  className="text-xs text-slate-600 cursor-pointer select-none"
                >
                  Remember me
                </label>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={submitting}
                className="w-full mt-2 py-3 px-4 bg-[#002B55] hover:bg-[#001D3A] active:scale-[0.99] text-white text-xs sm:text-sm font-bold rounded-lg shadow-md hover:shadow-lg transition-all duration-150 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"
              >
                {submitting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Authenticating...</span>
                  </>
                ) : (
                  <span>Login</span>
                )}
              </button>
            </form>
          </div>

          {/* Footer Link */}
          <div className="mt-8 pt-4 border-t border-slate-100 text-center">
            <p className="text-xs text-slate-500">
              Don't have an account?{" "}
              <Link
                href="/signup"
                className="font-bold text-[#002B55] hover:underline transition"
              >
                Request Access
              </Link>
            </p>
          </div>
        </div>

        {/* Right Side: Hero Image Banner */}
        <div className="relative hidden md:flex flex-col justify-end p-8 lg:p-10 bg-slate-950 overflow-hidden min-h-[500px]">
          {/* Background Hero Image */}
          <img
            src="/Images/Hero-img.png"
            alt="HDFC LLM Pipeline"
            className="absolute inset-0 w-full h-full object-cover object-center"
          />

          {/* Gradient Overlay for Text Readability */}
          <div className="absolute inset-0 bg-gradient-to-t from-[#001830] via-[#001830]/60 to-transparent" />

          {/* Overlay Content */}
          <div className="relative z-10">
            <h2 className="text-xl lg:text-2xl font-bold tracking-tight text-white leading-snug">
              Powering Institutional Intelligence
            </h2>
            <p className="text-xs lg:text-sm text-slate-200/90 mt-2 font-normal leading-relaxed max-w-sm">
              Advanced language models engineered for secure, high-stakes financial operations and strategic decision making.
            </p>
          </div>

          {/* Brand Watermark bottom right */}
          <div className="absolute bottom-4 right-5 z-10 pointer-events-none opacity-40">
            <span className="text-[10px] font-bold tracking-widest text-white uppercase">
              HDFC LLM Forge
            </span>
          </div>
        </div>

      </div>
    </div>
  );
}
