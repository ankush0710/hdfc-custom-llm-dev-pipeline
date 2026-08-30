"use client";

import { useAuth } from "@/app/context/AuthContext";
import { Loader2, ShieldAlert } from "lucide-react";
import Button from "@/components/ui/Button";
import { useRouter } from "next/navigation";

export default function ProtectedRoute({ children, allowedRoles = [] }) {
  const { user, isAuthenticated, loading, role, hasRole } = useAuth();
  const router = useRouter();

  if (loading) {
    return (
      <div className="flex h-96 w-full items-center justify-center lg:ml-[280px]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (allowedRoles.length > 0 && !hasRole(...allowedRoles)) {
    return (
      <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-4 lg:px-8 lg:ml-[280px] pb-16">
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-8 text-center max-w-xl mx-auto shadow-sm">
          <ShieldAlert className="mx-auto h-12 w-12 text-amber-600 mb-3" />
          <h2 className="text-xl font-extrabold text-amber-950">Access Restricted</h2>
          <p className="text-xs text-amber-800 mt-2 leading-relaxed">
            Your current role is <span className="font-bold uppercase font-mono px-2 py-0.5 rounded bg-amber-200 text-amber-900">{role}</span>.
            This action requires one of the following permissions: <span className="font-bold">{allowedRoles.join(", ")}</span>.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Button variant="default" onClick={() => router.back()}>
              Go Back
            </Button>
            <Button variant="primary" onClick={() => router.push("/")}>
              Return to Dashboard
            </Button>
          </div>
        </div>
      </main>
    );
  }

  return <>{children}</>;
}
