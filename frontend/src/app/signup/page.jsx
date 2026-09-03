"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { User, Mail, ShieldCheck, Lock, Eye, EyeOff, Loader2, Sparkles, ChevronDown } from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";
import { getApiErrorMessage } from "@/app/services/apiClient";
import { toast } from "sonner";

const ACCOUNT_TYPES = [
  {
    value: "DS",
    label: "Data Scientist",
    description: "Full access to train, fine-tune models, and manage datasets",
  },
  {
    value: "REVIEWER",
    label: "Reviewer",
    description: "Access to evaluate metrics, benchmark models, and review artifacts",
  },
  {
    value: "VIEWER",
    label: "Viewer / Customer",
    description: "Read-only access to explore dashboards, play with models, and view stats",
  },
];

export default function SignupPage() {
  const router = useRouter();
  const { signup, isAuthenticated, loading: authLoading } = useAuth();

  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    type: "DS",
    password: "",
    confirm_password: "",
  });

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

    const fullNameClean = formData.full_name.trim();
    const emailClean = formData.email.trim();
    const passwordClean = formData.password;
    const confirmPasswordClean = formData.confirm_password;

    if (!fullNameClean || !emailClean) {
      setError("Please provide your full name and work email.");
      return;
    }

    if (!passwordClean || !confirmPasswordClean) {
      setError("Please set and confirm your password.");
      return;
    }

    if (passwordClean.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (passwordClean !== confirmPasswordClean) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setSubmitting(true);
      await signup(
        fullNameClean,
        emailClean,
        passwordClean,
        confirmPasswordClean,
        formData.type
      );


      const roleLabel =
        ACCOUNT_TYPES.find((t) => t.value === formData.type)?.label || "User";

      toast.success("Account Created Successfully!", {
        description: `Request registered for ${roleLabel}. You can now log in to the platform.`,
      });

      router.replace("/login");
    } catch (err) {
      console.error("Signup error:", err);
      const msg = getApiErrorMessage(err, "Failed to submit registration request.");
      setError(msg);
      toast.error("Registration Failed", { description: msg });
    } finally {
      setSubmitting(false);
    }
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
      {/* Left Side: Signup Form (Full Height Split Screen) */}
      <div className="w-full md:w-1/2 min-h-screen flex flex-col justify-between p-6 sm:p-10 lg:p-12 bg-white text-slate-800 z-10 shadow-2xl overflow-y-auto shrink-0">
        {/* Brand Header */}
        <div className="flex items-center justify-between gap-3">
          <div className="h-14 w-35 flex items-center justify-center overflow-hidden">
            <img
              src="/images/HDFC-Bank-Logo.png"
              alt="HDFC Bank"
              className="h-full w-full object-contain"
            />
          </div>
          <div>
            <span className="text-base font-bold tracking-tight text-[#002B55] block">
              HDFC Bank
            </span>
            <span className="text-[11px] text-slate-500 font-medium block">
              Enterprise LLM Development Platform
            </span>
          </div>
        </div>

        {/* Center Form Area */}
        <div className="my-auto py-5 max-w-md w-full mx-auto">
          {/* Header */}
          <div className="mb-5">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Create an Account
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 font-normal leading-relaxed">
              Register for institutional access to custom LLM pipelines.
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700 font-medium animate-fadeIn">
              {error}
            </div>
          )}

          {/* Form with strictly requested fields */}
          <form onSubmit={handleSubmit} className="space-y-3.5">
            {/* 1. Full Name */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Full Name
              </label>
              <div className="relative flex items-center">
                <User
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                  size={16}
                />
                <input
                  type="text"
                  required
                  placeholder="e.g. Rahul Sharma"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full pl-10 pr-4 py-2 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
                />
              </div>
            </div>

            {/* 2. Email */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Work Email
              </label>
              <div className="relative flex items-center">
                <Mail
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                  size={16}
                />
                <input
                  type="email"
                  required
                  placeholder="name@hdfcbank.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full pl-10 pr-4 py-2 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
                />
              </div>
            </div>

            {/* 3. Account Type (Data Scientist, Reviewer, Viewer/Customer) */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Account Type
              </label>
              <div className="relative flex items-center">
                <ShieldCheck
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                  size={16}
                />
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full pl-10 pr-9 py-2 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition cursor-pointer appearance-none font-medium"
                >
                  {ACCOUNT_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
                <ChevronDown
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                  size={15}
                />
              </div>
              <p className="text-[11px] text-slate-500 mt-1 pl-1">
                {ACCOUNT_TYPES.find((t) => t.value === formData.type)?.description}
              </p>
            </div>

            {/* 4 & 5. Password and Confirm Password */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {/* Password */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Password
                </label>
                <div className="relative flex items-center">
                  <Lock
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                    size={15}
                  />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    placeholder="Min 8 characters"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full pl-8 pr-3 py-2 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
                  />
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-semibold text-slate-700">
                    Confirm Password
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-[11px] font-medium text-slate-500 hover:text-[#002B55] cursor-pointer"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
                <div className="relative flex items-center">
                  <Lock
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                    size={15}
                  />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    placeholder="Re-enter password"
                    value={formData.confirm_password}
                    onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                    className="w-full pl-8 pr-3 py-2 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
                  />
                </div>
              </div>
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
                  <span>Submitting Request...</span>
                </>
              ) : (
                <span>Request Access</span>
              )}
            </button>
          </form>
        </div>

        {/* Footer Link */}
        <div className="pt-4 border-t border-slate-100 text-center max-w-md w-full mx-auto">
          <p className="text-xs sm:text-sm text-slate-500">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-bold text-[#002B55] hover:underline transition"
            >
              Sign In
            </Link>
          </p>
        </div>
      </div>
      {/* Right Side: Fullscreen Hero Image Section covering entire div */}
      <div className="relative hidden md:flex md:w-1/2 flex-col justify-between p-8 lg:p-12 xl:p-16 bg-slate-950 overflow-hidden min-h-screen">
        {/* Hero image covering 100% of the entire container */}
        <img
          src="/images/Hero-img.png"
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

          <div className="mt-5 grid grid-cols-3 gap-3 text-xs text-white/80 font-mono pt-4 border-t border-white/10">
            <div className="p-2 rounded-lg bg-white/5 border border-white/10 backdrop-blur-sm text-center">
              <span className="block text-xs font-bold text-white">DS Role</span>
              <span className="text-[10px] text-slate-300">Fine-Tuning</span>
            </div>
            <div className="p-2 rounded-lg bg-white/5 border border-white/10 backdrop-blur-sm text-center">
              <span className="block text-xs font-bold text-white">Reviewer</span>
              <span className="text-[10px] text-slate-300">Benchmarks</span>
            </div>
            <div className="p-2 rounded-lg bg-white/5 border border-white/10 backdrop-blur-sm text-center">
              <span className="block text-xs font-bold text-white">Viewer</span>
              <span className="text-[10px] text-slate-300">Inference</span>
            </div>
          </div>
        </div>
      </div>

      {/* Brand Watermark Bottom Right */}
      <div className="absolute bottom-4 right-8 z-10 pointer-events-none">
        <span className="text-white opacity-50 text-xs font-bold tracking-tight">HDFC Bank</span>
      </div>
    </div>
  );
}
