"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { User, Mail, Building2, FileText, Lock, Eye, EyeOff, Loader2 } from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";
import { getApiErrorMessage } from "@/app/services/apiClient";
import { toast } from "sonner";

export default function SignupPage() {
  const router = useRouter();
  const { signup, isAuthenticated, loading: authLoading } = useAuth();

  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    department: "",
    purpose: "Model Fine-Tuning & Evaluation",
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
    e.preventDefault();
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
        confirmPasswordClean
      );

      toast.success("Access Request Submitted!", {
        description: "Account created successfully with default VIEWER access. You can now log in.",
      });

      router.replace("/login");
    } catch (err) {
      console.error("Signup error:", err);
      const msg = getApiErrorMessage(err, "Failed to submit access request.");
      setError(msg);
      toast.error("Request Failed", { description: msg });
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
        <div className="p-8 sm:p-10 lg:p-11 flex flex-col justify-between bg-white text-slate-800">
          <div>
            {/* Logo and Brand */}
            <div className="flex items-center gap-2.5 mb-6">
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
            <div className="mb-5">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Request Access
              </h1>
              <p className="text-xs sm:text-sm text-slate-500 mt-1 font-normal">
                Apply for enterprise access to the pipeline.
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-700 font-medium animate-fadeIn">
                {error}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3">
              {/* Full Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Full Name
                </label>
                <div className="relative flex items-center">
                  <User
                    className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                    size={15}
                  />
                  <input
                    type="text"
                    required
                    placeholder="e.g. Rahul Sharma"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full pl-10 pr-4 py-2 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
                  />
                </div>
              </div>

              {/* Work Email */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Work Email
                </label>
                <div className="relative flex items-center">
                  <Mail
                    className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                    size={15}
                  />
                  <input
                    type="email"
                    required
                    placeholder="name@hdfcbank.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full pl-10 pr-4 py-2 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
                  />
                </div>
              </div>

              {/* Organization / Department */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Organization / Department
                </label>
                <div className="relative flex items-center">
                  <Building2
                    className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                    size={15}
                  />
                  <input
                    type="text"
                    placeholder="e.g. Risk Assessment / AI Lab"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    className="w-full pl-10 pr-4 py-2 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
                  />
                </div>
              </div>

              {/* Purpose of Use */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Purpose of Use
                </label>
                <div className="relative flex items-center">
                  <FileText
                    className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                    size={15}
                  />
                  <select
                    value={formData.purpose}
                    onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                    className="w-full pl-10 pr-4 py-2 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition cursor-pointer appearance-none"
                  >
                    <option value="Model Fine-Tuning & Evaluation">Model Fine-Tuning & Evaluation</option>
                    <option value="Banking Operations Automation">Banking Operations Automation</option>
                    <option value="Risk & Fraud Intelligence">Risk & Fraud Intelligence</option>
                    <option value="Customer Journey AI">Customer Journey AI</option>
                    <option value="Enterprise Research">Enterprise Research</option>
                  </select>
                </div>
              </div>

              {/* Password Fields */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Password
                  </label>
                  <div className="relative flex items-center">
                    <Lock
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                      size={14}
                    />
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full pl-8 pr-3 py-2 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs font-semibold text-slate-700">
                      Confirm
                    </label>
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-[10px] font-medium text-slate-500 hover:text-[#002B55] cursor-pointer"
                    >
                      {showPassword ? "Hide" : "Show"}
                    </button>
                  </div>
                  <div className="relative flex items-center">
                    <Lock
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                      size={14}
                    />
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      placeholder="••••••••"
                      value={formData.confirm_password}
                      onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                      className="w-full pl-8 pr-3 py-2 bg-slate-50 hover:bg-slate-50/80 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#002B55]/20 focus:border-[#002B55] focus:bg-white transition"
                    />
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={submitting}
                className="w-full mt-3 py-2.5 px-4 bg-[#002B55] hover:bg-[#001D3A] active:scale-[0.99] text-white text-xs sm:text-sm font-bold rounded-lg shadow-md hover:shadow-lg transition-all duration-150 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"
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
          <div className="mt-6 pt-3 border-t border-slate-100 text-center">
            <p className="text-xs text-slate-500">
              Already have an account?{" "}
              <Link
                href="/login"
                className="font-bold text-[#002B55] hover:underline transition"
              >
                Login
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
              Empowering Financial Intelligence
            </h2>
            <p className="text-xs lg:text-sm text-slate-200/90 mt-2 font-normal leading-relaxed max-w-sm">
              Secure, compliant, and highly optimized foundational model infrastructure designed exclusively for enterprise banking requirements.
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
