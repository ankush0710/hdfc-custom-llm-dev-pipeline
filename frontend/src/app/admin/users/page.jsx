"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useAuth } from "@/app/context/AuthContext";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import {
  getUsers,
  updateUserRole,
  updateUserStatus,
} from "@/app/services/authService/authServices";
import {
  Users,
  ShieldCheck,
  UserCheck,
  UserX,
  Search,
  RefreshCw,
  Clock,
  Mail,
  Sparkles,
  AlertCircle,
} from "lucide-react";
import Button from "@/components/ui/Button";
import { toast } from "sonner";

const ROLES = ["ADMIN", "DS", "REVIEWER", "VIEWER"];

export default function UserManagementPage() {
  return (
    <ProtectedRoute allowedRoles={["ADMIN"]}>
      <UserManagementContent />
    </ProtectedRoute>
  );
}

function UserManagementContent() {
  const { user: currentUser, refreshProfile } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [updatingUserId, setUpdatingUserId] = useState(null);

  // Fetch real users from PostgreSQL backend
  const fetchUsersList = useCallback(async (isSilent = false) => {
    try {
      if (!isSilent) setLoading(true);
      else setRefreshing(true);

      const data = await getUsers();
      setUsers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load platform users:", err);
      const msg = err?.response?.data?.detail || "Failed to load platform users.";
      toast.error("Failed to fetch users", { description: msg });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchUsersList();
  }, [fetchUsersList]);

  // Handle role update
  const handleRoleChange = async (userId, targetUserEmail, newRole) => {
    try {
      setUpdatingUserId(userId);
      const updatedUser = await updateUserRole(userId, newRole);

      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, role: updatedUser.role } : u))
      );

      toast.success("Role updated successfully", {
        description: `User ${targetUserEmail} is now assigned ${newRole}.`,
      });

      // If current user modified their own record, refresh auth state
      if (currentUser?.id === userId) {
        await refreshProfile();
      }
    } catch (err) {
      console.error("Failed to update role:", err);
      const msg = err?.response?.data?.detail || "Failed to update role.";
      toast.error("Role update failed", { description: msg });
    } finally {
      setUpdatingUserId(null);
    }
  };

  // Handle account status toggle (activate / deactivate)
  const handleStatusToggle = async (userId, targetUserEmail, currentStatus) => {
    const nextStatus = !currentStatus;

    if (
      !nextStatus &&
      !window.confirm(
        `Are you sure you want to deactivate user "${targetUserEmail}"? They will not be able to log in.`
      )
    ) {
      return;
    }

    try {
      setUpdatingUserId(userId);
      const updatedUser = await updateUserStatus(userId, nextStatus);

      setUsers((prev) =>
        prev.map((u) =>
          u.id === userId ? { ...u, is_active: updatedUser.is_active } : u
        )
      );

      toast.success(`Account ${nextStatus ? "Activated" : "Deactivated"}`, {
        description: `User ${targetUserEmail} status has been updated.`,
      });
    } catch (err) {
      console.error("Failed to toggle status:", err);
      const msg = err?.response?.data?.detail || "Failed to update user status.";
      toast.error("Status update failed", { description: msg });
    } finally {
      setUpdatingUserId(null);
    }
  };

  // Quick promote to ADMIN handler
  const handlePromoteToAdmin = async (userId, targetUserEmail) => {
    if (
      !window.confirm(
        `Promote "${targetUserEmail}" to ADMIN?\n\nThis user will receive full administrative access to all ML pipeline services and user management.`
      )
    ) {
      return;
    }
    await handleRoleChange(userId, targetUserEmail, "ADMIN");
  };

  // Filtered users
  const filteredUsers = useMemo(() => {
    return users.filter((u) => {
      // 1. Search Query
      const q = searchQuery.toLowerCase().trim();
      const matchSearch =
        !q ||
        (u.full_name || "").toLowerCase().includes(q) ||
        (u.email || "").toLowerCase().includes(q);

      // 2. Role Filter
      const userRole = (u.role || "").toUpperCase();
      const normUserRole = userRole === "DATA_SCIENTIST" ? "DS" : userRole;
      const matchRole = roleFilter === "ALL" || normUserRole === roleFilter;

      // 3. Status Filter
      const matchStatus =
        statusFilter === "ALL" ||
        (statusFilter === "ACTIVE" && u.is_active) ||
        (statusFilter === "INACTIVE" && !u.is_active);

      return matchSearch && matchRole && matchStatus;
    });
  }, [users, searchQuery, roleFilter, statusFilter]);

  // Aggregate stats
  const stats = useMemo(() => {
    const total = users.length;
    let admins = 0;
    let ds = 0;
    let reviewers = 0;
    let viewers = 0;
    let active = 0;

    users.forEach((u) => {
      const r = (u.role || "").toUpperCase();
      if (r === "ADMIN") admins++;
      else if (r === "DS" || r === "DATA_SCIENTIST") ds++;
      else if (r === "REVIEWER") reviewers++;
      else viewers++;

      if (u.is_active) active++;
    });

    return { total, admins, ds, reviewers, viewers, active };
  }, [users]);

  // Role Badge Styling Helper
  const getRoleBadgeStyle = (role) => {
    const norm = (role || "").toUpperCase();
    switch (norm) {
      case "ADMIN":
        return "bg-red-50 text-red-700 border-red-200 ring-1 ring-red-200/50";
      case "DS":
      case "DATA_SCIENTIST":
        return "bg-purple-50 text-purple-700 border-purple-200 ring-1 ring-purple-200/50";
      case "REVIEWER":
        return "bg-amber-50 text-amber-700 border-amber-200 ring-1 ring-amber-200/50";
      case "VIEWER":
      default:
        return "bg-blue-50 text-blue-700 border-blue-200 ring-1 ring-blue-200/50";
    }
  };

  return (
    <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-4 lg:px-8 lg:ml-[280px] pb-16">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#002B55] text-white shadow-sm">
              <Users size={18} />
            </div>
            <h1 className="text-2xl lg:text-3xl font-extrabold text-gray-900 tracking-tight">
              User Management
            </h1>
          </div>
          <p className="text-xs lg:text-sm text-gray-500 mt-1 font-medium">
            Manage enterprise team accounts, govern role-based authorizations, and promote platform administrators.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="default"
            icon={RefreshCw}
            onClick={() => fetchUsersList(true)}
            disabled={refreshing || loading}
            className={refreshing ? "[&>svg]:animate-spin [&>svg]:text-blue-600" : ""}
          >
            {refreshing ? "Refreshing..." : "Refresh"}
          </Button>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {/* Total Users */}
        <div className="bg-white rounded-2xl border border-gray-200/80 p-5 shadow-sm">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-400">
            <span>Total Accounts</span>
            <Users size={16} className="text-blue-600" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="font-mono text-2xl font-extrabold text-gray-900">
              {loading ? "..." : stats.total}
            </span>
            <span className="text-xs font-medium text-emerald-600">
              {stats.active} active
            </span>
          </div>
        </div>

        {/* Administrators */}
        <div className="bg-white rounded-2xl border border-gray-200/80 p-5 shadow-sm border-l-4 border-l-red-500">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-400">
            <span>Administrators</span>
            <ShieldCheck size={16} className="text-red-600" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="font-mono text-2xl font-extrabold text-gray-900">
              {loading ? "..." : stats.admins}
            </span>
            <span className="text-[11px] text-gray-400 font-medium">
              Full Privileges
            </span>
          </div>
        </div>

        {/* Data Scientists */}
        <div className="bg-white rounded-2xl border border-gray-200/80 p-5 shadow-sm border-l-4 border-l-purple-500">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-400">
            <span>Data Scientists</span>
            <Sparkles size={16} className="text-purple-600" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="font-mono text-2xl font-extrabold text-gray-900">
              {loading ? "..." : stats.ds}
            </span>
            <span className="text-[11px] text-gray-400 font-medium">
              Pipeline Training
            </span>
          </div>
        </div>

        {/* Reviewers & Viewers */}
        <div className="bg-white rounded-2xl border border-gray-200/80 p-5 shadow-sm border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-400">
            <span>Reviewers & Viewers</span>
            <UserCheck size={16} className="text-blue-600" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="font-mono text-2xl font-extrabold text-gray-900">
              {loading ? "..." : stats.reviewers + stats.viewers}
            </span>
            <span className="text-[11px] text-gray-400 font-medium">
              {stats.reviewers} Rev · {stats.viewers} View
            </span>
          </div>
        </div>
      </div>

      {/* Filter and Search Toolbar */}
      <div className="bg-white rounded-2xl border border-gray-200/80 p-4 mb-6 shadow-sm flex flex-col md:flex-row gap-4 justify-between items-center">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
          <input
            type="text"
            placeholder="Search by name or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-xs bg-slate-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Role Filter */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-gray-500 font-medium">Role:</span>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="bg-slate-50 border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs text-gray-700 font-medium focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              <option value="ALL">All Roles</option>
              <option value="ADMIN">ADMIN</option>
              <option value="DS">DS (Data Scientist)</option>
              <option value="REVIEWER">REVIEWER</option>
              <option value="VIEWER">VIEWER</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-gray-500 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-50 border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs text-gray-700 font-medium focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active Only</option>
              <option value="INACTIVE">Deactivated Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-2xl border border-gray-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex flex-col items-center justify-center p-16 text-center">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mb-3" />
            <p className="text-sm text-gray-600 font-medium">
              Loading platform accounts from database...
            </p>
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-16 text-center">
            <AlertCircle size={32} className="text-gray-400 mb-2" />
            <h3 className="text-base font-semibold text-gray-800">No users found</h3>
            <p className="text-xs text-gray-500 mt-1 max-w-sm">
              {searchQuery || roleFilter !== "ALL" || statusFilter !== "ALL"
                ? "Try clearing your filters or search terms."
                : "No registered accounts found in the database."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FAFBFE] text-gray-600 font-bold uppercase tracking-wider border-b border-gray-200 text-[11px]">
                <tr>
                  <th className="px-6 py-3.5">User</th>
                  <th className="px-6 py-3.5">Email</th>
                  <th className="px-6 py-3.5">Assigned Role</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Registered</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 font-medium text-gray-700">
                {filteredUsers.map((u) => {
                  const isCurrent = currentUser?.id === u.id;
                  const isBusy = updatingUserId === u.id;
                  const rawRole = (u.role || "").toUpperCase();
                  const normRole = rawRole === "DATA_SCIENTIST" ? "DS" : rawRole;
                  const formattedDate = u.created_at
                    ? new Date(u.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })
                    : "—";

                  return (
                    <tr
                      key={u.id}
                      className={`hover:bg-slate-50/70 transition-colors ${
                        !u.is_active ? "bg-slate-50/40 text-gray-400" : ""
                      }`}
                    >
                      {/* Name with Initials Avatar */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div
                            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-white font-bold text-xs ${
                              normRole === "ADMIN"
                                ? "bg-red-600 shadow-sm"
                                : normRole === "DS"
                                ? "bg-purple-600"
                                : normRole === "REVIEWER"
                                ? "bg-amber-600"
                                : "bg-blue-600"
                            }`}
                          >
                            {u.full_name ? u.full_name.charAt(0).toUpperCase() : "U"}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-gray-900 text-sm">
                                {u.full_name}
                              </span>
                              {isCurrent && (
                                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-700">
                                  You
                                </span>
                              )}
                            </div>
                            <span className="text-[11px] text-gray-400 font-mono">
                              User ID #{u.id}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Email */}
                      <td className="px-6 py-4 font-mono text-gray-700">
                        <div className="flex items-center gap-1.5">
                          <Mail size={13} className="text-gray-400 shrink-0" />
                          <span>{u.email}</span>
                        </div>
                      </td>

                      {/* Current Role + Selector */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span
                            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-mono font-bold border ${getRoleBadgeStyle(
                              normRole
                            )}`}
                          >
                            <ShieldCheck size={12} />
                            <span>{normRole}</span>
                          </span>

                          {/* Role Change Dropdown */}
                          <select
                            disabled={isBusy}
                            value={normRole}
                            onChange={(e) =>
                              handleRoleChange(u.id, u.email, e.target.value)
                            }
                            className="bg-white border border-gray-200 rounded-lg px-2 py-1 text-xs text-gray-800 font-semibold focus:outline-none focus:ring-2 focus:ring-blue-600 cursor-pointer disabled:opacity-50"
                          >
                            {ROLES.map((r) => (
                              <option key={r} value={r}>
                                {r}
                              </option>
                            ))}
                          </select>
                        </div>
                      </td>

                      {/* Account Status */}
                      <td className="px-6 py-4">
                        {u.is_active ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600 animate-pulse" />
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                            <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
                            Deactivated
                          </span>
                        )}
                      </td>

                      {/* Registered Date */}
                      <td className="px-6 py-4 text-gray-500 font-mono">
                        <div className="flex items-center gap-1.5">
                          <Clock size={13} className="text-gray-400" />
                          <span>{formattedDate}</span>
                        </div>
                      </td>

                      {/* Action Buttons */}
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {/* Quick Promote to Admin Button */}
                          {normRole !== "ADMIN" && (
                            <button
                              type="button"
                              disabled={isBusy || !u.is_active}
                              onClick={() => handlePromoteToAdmin(u.id, u.email)}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-red-200 bg-red-50 hover:bg-red-100 text-red-700 font-bold text-xs transition disabled:opacity-40 cursor-pointer"
                              title="Promote this user to Administrator"
                            >
                              <ShieldCheck size={13} />
                              <span>Make Admin</span>
                            </button>
                          )}

                          {/* Status Toggle Button */}
                          <button
                            type="button"
                            disabled={isBusy || (isCurrent && u.is_active)}
                            onClick={() =>
                              handleStatusToggle(u.id, u.email, u.is_active)
                            }
                            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold border transition disabled:opacity-40 cursor-pointer ${
                              u.is_active
                                ? "border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700"
                                : "border-emerald-200 bg-emerald-50 hover:bg-emerald-100 text-emerald-700"
                            }`}
                            title={
                              isCurrent && u.is_active
                                ? "Cannot deactivate yourself"
                                : u.is_active
                                ? "Deactivate account"
                                : "Activate account"
                            }
                          >
                            {u.is_active ? (
                              <>
                                <UserX size={13} />
                                <span>Deactivate</span>
                              </>
                            ) : (
                              <>
                                <UserCheck size={13} />
                                <span>Activate</span>
                              </>
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
