"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Lock, User, Eye, EyeOff, Loader2, Sparkles, ShieldCheck } from "lucide-react";
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
    <div className="min-h-screen w-full flex flex-col md:flex-row bg-[#030712] overflow-hidden">
      {/* Left Side: Login Form (Full Height Split Screen) */}
      <div className="w-full md:w-1/2 min-h-screen flex flex-col justify-between p-6 sm:p-10 lg:p-14 bg-white text-slate-800 z-10 shadow-2xl overflow-y-auto shrink-0">
        {/* Brand Header */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-[#002B55] flex items-center justify-center overflow-hidden p-1.5 shadow-md">
            <img
              src="/Images/HDFC_Forge_logo.png"
              alt="HDFC LLM Forge"
              className="h-full w-full object-contain"
            />
          </div>
          <div>
            <span className="text-base font-bold tracking-tight text-[#002B55] block">
              HDFC LLM Forge
            </span>
            <span className="text-[11px] text-slate-500 font-medium block">
              Enterprise LLM Development Platform
            </span>
          </div>
        </div>

        {/* Center Form Area */}
        <div className="my-auto py-6 max-w-md w-full mx-auto">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Welcome Back
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1.5 font-normal leading-relaxed">
              Sign in to access your models, datasets, and AI fine-tuning pipelines.
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="mb-5 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-700 font-medium animate-fadeIn">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username / Email */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Username / Email Address
              </label>
              <div className="relative flex items-center">
                <User
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                  size={16}
                />
                <input
                  type="text"
                  required
                  placeholder="name@hdfcbank.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
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
                  className="text-xs font-medium text-slate-500 hover:text-[#002B55] hover:underline transition cursor-pointer"
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
                  className="w-full pl-10 pr-10 py-2.5 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition cursor-pointer p-1"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
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
                Remember me on this workstation
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={submitting}
              className="w-full mt-2 py-3 px-4 bg-[#002B55] hover:bg-[#001D3A] active:scale-[0.99] text-white text-xs sm:text-sm font-bold rounded-xl shadow-md hover:shadow-lg transition-all duration-150 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"
            >
              {submitting ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>Sign In</span>
              )}
            </button>
          </form>
        </div>

        {/* Footer Link */}
        <div className="pt-4 border-t border-slate-100 text-center max-w-md w-full mx-auto">
          <p className="text-xs sm:text-sm text-slate-500">
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

      {/* Right Side: Fullscreen Hero Image Section covering entire div */}
      <div className="relative hidden md:flex md:w-1/2 flex-col justify-between p-8 lg:p-12 xl:p-16 bg-slate-950 overflow-hidden min-h-screen">
        {/* Hero image covering 100% of the entire container */}
        <img
          src="/Images/Hero-img.png"
          alt="HDFC LLM Pipeline"
          className="absolute inset-0 w-full h-full object-cover object-center"
        />

        {/* High contrast gradient overlays */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#001428] via-[#001428]/40 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#001428]/50 via-transparent to-transparent" />

        {/* Bottom Hero Text Card */}
        <div className="absolute bottom-4 right-4 left-4 z-10 max-w-xl backdrop-blur-md p-6 lg:p-8 rounded-2xl border border-white/15 shadow-2xl">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-500/20 border border-blue-400/30 text-blue-300 text-[11px] font-semibold tracking-wider uppercase mb-2.5">
            <Sparkles size={12} />
            Next-Gen LLM Infrastructure
          </div>
          <h2 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-white tracking-tight leading-tight">
            Powering Institutional Intelligence
          </h2>
          <p className="text-xs sm:text-sm text-slate-200/90 mt-2 font-normal leading-relaxed">
            Fine-tune, evaluate, benchmark, and deploy enterprise-grade custom language models with bank-level security and governance.
          </p>

          <div className="mt-5 flex items-center gap-6 text-xs text-white/80 font-mono pt-4 border-t border-white/10">
            <div>
              <span className="block text-sm sm:text-base font-bold text-white">99.9%</span>
              <span className="text-[11px] text-slate-300">Uptime SLA</span>
            </div>
            <div className="h-6 w-px bg-white/20" />
            <div>
              <span className="block text-sm sm:text-base font-bold text-white">Zero</span>
              <span className="text-[11px] text-slate-300">Data Retention</span>
            </div>
            <div className="h-6 w-px bg-white/20" />
            <div>
              <span className="block text-sm sm:text-base font-bold text-white">Full</span>
              <span className="text-[11px] text-slate-300">Auditability</span>
            </div>
          </div>
        </div>

        {/* Brand Watermark Bottom Right */}
        <div className="absolute bottom-4 right-6 z-10 pointer-events-none opacity-40">
          <span className="text-[10px] font-bold tracking-widest text-white uppercase font-mono">
            HDFC LLM Forge
          </span>
        </div>
      </div>
    </div>
  );
}
