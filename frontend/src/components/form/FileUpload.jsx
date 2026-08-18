"use client";

import { useRef, useState } from "react";
import { CloudUpload } from "lucide-react";

const FileUpload = ({ onFileSelect }) => {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);

  const handleFile = (selectedFile) => {
    if (!selectedFile) return;

    setFile(selectedFile);
    onFileSelect?.(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files?.[0];

    if (droppedFile) {
      handleFile(droppedFile);
    }
  };

  const handleBrowse = (e) => {
    const selectedFile = e.target.files?.[0];

    if (selectedFile) {
      handleFile(selectedFile);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <label className="text-[14px] font-medium uppercase tracking-wide text-[#002B5C]">
        File Upload
      </label>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`flex min-h-[176px] flex-col items-center justify-center rounded-md border border-dashed px-4 py-6 transition ${
          isDragging
            ? "border-[#004C97] bg-blue-50"
            : "border-slate-300 bg-[#F8F9FC]"
        }`}
      >
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100  cursor-pointer">
          <CloudUpload size={21} className="text-[#004C97]" />
        </div>

        {file ? (
          <>
            <p className="text-sm font-medium text-[#002B5C]">{file.name}</p>

            <p className="mt-1 text-[11px] text-slate-500">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </>
        ) : (
          <>
            <p className="text-sm font-medium text-[#002B5C]">
              Drag and drop files here
            </p>

            <p className="mt-1 text-[12px] text-slate-500">
              Support for .csv, .jsonl. Maximum file size 5GB.
            </p>
          </>
        )}

        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="mt-3 rounded-sm border border-slate-300 bg-white px-3 py-1.5 text-[14px] font-medium text-[#002B5C] transition hover:bg-slate-50 cursor-pointer"
        >
          Browse Files
        </button>

        <input
          ref={inputRef}
          type="file"
          accept=".csv,.jsonl,.pdf,.xlsx"
          onChange={handleBrowse}
          className="hidden"
        />
      </div>
    </div>
  );
};

export default FileUpload;
