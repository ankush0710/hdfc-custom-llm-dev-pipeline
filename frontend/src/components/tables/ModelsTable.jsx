"use client";

import { MoreVertical, Filter, ChevronLeft, ChevronRight, Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { useMemo, useState, useEffect } from "react";

export default function ModelsTable({
  data = [],
  columns = [],
  pageSize = 5,
  title = "Recent Datasets",
  showFilter = true,
  showMenu = true,
  filterOptions = [],
  selectedFilter = "ALL",
  onFilterChange = null,
  loading = false,
  error = null,
  onRetry = null,
  emptyMessage = "No records available",
}) {
  const [currentPage, setCurrentPage] = useState(1);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Total number of pages (at least 1)
  const totalPages = Math.max(1, Math.ceil(data.length / pageSize));

  // Reset or adjust current page if out of bounds after data changes
  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [totalPages, currentPage]);

  // Data for current page (only pageSize items visible)
  const currentData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return data.slice(startIndex, endIndex);
  }, [data, currentPage, pageSize]);

  // Generate visible page numbers (smart ellipsis for large page counts)
  const visiblePages = useMemo(() => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }
    if (currentPage <= 4) {
      return [1, 2, 3, 4, 5, "...", totalPages];
    }
    if (currentPage >= totalPages - 3) {
      return [
        1,
        "...",
        totalPages - 4,
        totalPages - 3,
        totalPages - 2,
        totalPages - 1,
        totalPages,
      ];
    }
    return [
      1,
      "...",
      currentPage - 1,
      currentPage,
      currentPage + 1,
      "...",
      totalPages,
    ];
  }, [totalPages, currentPage]);

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
            {data.length} Total
          </span>
        </div>

        <div className="flex items-center gap-3 relative">
          {showFilter && (
            <div className="relative">
              <button
                type="button"
                onClick={() => {
                  if (filterOptions && filterOptions.length > 0) {
                    setIsFilterOpen((prev) => !prev);
                  } else if (onFilterChange) {
                    onFilterChange();
                  }
                }}
                className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-lg border transition ${
                  selectedFilter !== "ALL"
                    ? "bg-blue-50 border-blue-200 text-blue-700"
                    : "text-gray-600 border-gray-200 hover:bg-gray-100"
                }`}
                title="Filter by status"
              >
                <Filter size={14} />
                <span>
                  {selectedFilter !== "ALL"
                    ? filterOptions.find((o) => o.value === selectedFilter)?.label || selectedFilter
                    : "Filter"}
                </span>
              </button>

              {/* Filter Dropdown Popover */}
              {isFilterOpen && filterOptions.length > 0 && (
                <>
                  <div
                    className="fixed inset-0 z-20"
                    onClick={() => setIsFilterOpen(false)}
                  />
                  <div className="absolute right-0 mt-2 w-44 rounded-xl bg-white p-1.5 shadow-lg border border-gray-200 z-30 animate-in fade-in zoom-in-95 duration-150">
                    <p className="px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider text-gray-400">
                      Filter by Status
                    </p>
                    {filterOptions.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => {
                          if (onFilterChange) onFilterChange(opt.value);
                          setIsFilterOpen(false);
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 text-xs rounded-md transition text-left cursor-pointer ${
                          selectedFilter === opt.value
                            ? "bg-blue-50 text-blue-700 font-bold"
                            : "text-gray-700 hover:bg-gray-50 font-medium"
                        }`}
                      >
                        <span>{opt.label}</span>
                        {opt.count !== undefined && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
                            {opt.count}
                          </span>
                        )}
                      </button>
                    ))}

                    {selectedFilter !== "ALL" && (
                      <div className="pt-1 mt-1 border-t border-gray-100">
                        <button
                          type="button"
                          onClick={() => {
                            if (onFilterChange) onFilterChange("ALL");
                            setIsFilterOpen(false);
                          }}
                          className="w-full text-center py-1 text-[11px] font-semibold text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded cursor-pointer"
                        >
                          Reset Filter
                        </button>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {showMenu && (
            <button
              type="button"
              className="text-gray-500 transition hover:text-gray-700 p-1 rounded hover:bg-gray-100"
              title="More options"
            >
              <MoreVertical size={18} />
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          {/* Table Head */}
          <thead className="bg-blue-50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={`px-5 py-3 text-xs font-semibold uppercase text-gray-600 ${column.align === "right"
                      ? "text-right"
                      : column.align === "center"
                        ? "text-center"
                        : "text-left"
                    }`}
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>

          {/* Table Body */}
          <tbody>
            {loading ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-5 py-12 text-center"
                >
                  <div className="flex flex-col items-center justify-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin text-[#002B55]" />
                    <p className="text-xs font-semibold text-gray-500">
                      Loading data from backend...
                    </p>
                  </div>
                </td>
              </tr>
            ) : error ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-5 py-10 text-center"
                >
                  <div className="flex flex-col items-center justify-center gap-2 max-w-sm mx-auto">
                    <AlertCircle className="h-6 w-6 text-red-500" />
                    <p className="text-xs font-semibold text-red-600">
                      {typeof error === "string" ? error : "Failed to load records."}
                    </p>
                    {onRetry && (
                      <button
                        type="button"
                        onClick={onRetry}
                        className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800 underline"
                      >
                        <RefreshCw size={12} />
                        <span>Retry</span>
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ) : currentData.length > 0 ? (
              currentData.map((row, rowIndex) => (
                <tr
                  key={row.id ?? rowIndex}
                  className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`px-5 py-4 text-sm text-gray-700 ${column.align === "right"
                          ? "text-right"
                          : column.align === "center"
                            ? "text-center"
                            : "text-left"
                        }`}
                    >
                      {/* Custom cell renderer */}
                      {column.render
                        ? column.render(row, rowIndex)
                        : row[column.key]}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-5 py-12 text-center text-sm text-gray-500"
                >
                  <div className="flex flex-col items-center justify-center gap-1.5 max-w-sm mx-auto text-center">
                    <p className="text-sm font-semibold text-gray-700">No records found</p>
                    <p className="text-xs text-gray-500">{emptyMessage}</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {data.length > 0 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-gray-200 px-5 py-3.5 bg-[#FAFBFE]">
          {/* Showing row count info */}
          <p className="text-xs sm:text-sm text-gray-500">
            Showing{" "}
            <span className="font-semibold text-gray-800">
              {(currentPage - 1) * pageSize + 1}
            </span>{" "}
            to{" "}
            <span className="font-semibold text-gray-800">
              {Math.min(currentPage * pageSize, data.length)}
            </span>{" "}
            of <span className="font-semibold text-gray-800">{data.length}</span>{" "}
            entries
          </p>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center gap-1.5">
              {/* Previous */}
              <button
                type="button"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                className="flex h-8 w-8 items-center justify-center rounded-md border border-gray-200 bg-white text-gray-600 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40"
                title="Previous page"
              >
                <ChevronLeft size={16} />
              </button>

              {/* Page Numbers */}
              {visiblePages.map((page, idx) => {
                if (page === "...") {
                  return (
                    <span
                      key={`ellipsis-${idx}`}
                      className="px-2 text-xs text-gray-400 font-bold"
                    >
                      ...
                    </span>
                  );
                }

                const isActive = currentPage === page;
                return (
                  <button
                    key={page}
                    type="button"
                    onClick={() => setCurrentPage(page)}
                    className={`h-8 min-w-8 rounded-md px-2.5 text-xs font-semibold transition cursor-pointer ${isActive
                        ? "bg-[#002B55] text-white shadow-sm"
                        : "border border-gray-200 bg-white text-gray-700 hover:bg-gray-100"
                      }`}
                  >
                    {page}
                  </button>
                );
              })}

              {/* Next */}
              <button
                type="button"
                disabled={currentPage === totalPages}
                onClick={() =>
                  setCurrentPage((prev) => Math.min(prev + 1, totalPages))
                }
                className="flex h-8 w-8 items-center justify-center rounded-md border border-gray-200 bg-white text-gray-600 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40"
                title="Next page"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
