"use client";

import React, { useState, useRef } from "react";
import { Upload, AlertCircle, CheckCircle, Loader } from "lucide-react";
import { apiClient } from "@/lib/api";

interface UploadStatus {
  id: string;
  filename: string;
  status: "pending" | "uploading" | "success" | "error";
  progress: number;
  error?: string;
}

export default function DocumentUploader({ onUploadSuccess }: { onUploadSuccess?: () => void }) {
  const [uploads, setUploads] = useState<UploadStatus[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const allowedTypes = [".pdf", ".docx", ".txt", ".csv"];

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const processFiles = async (files: FileList) => {
    const newUploads: UploadStatus[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const fileExt = "." + file.name.split(".").pop()?.toLowerCase();

      // Validate file type
      if (!allowedTypes.includes(fileExt)) {
        newUploads.push({
          id: `${file.name}-${Date.now()}`,
          filename: file.name,
          status: "error",
          progress: 0,
          error: `Unsupported file type: ${fileExt}`,
        });
        continue;
      }

      // Validate file size (100MB)
      if (file.size > 100 * 1024 * 1024) {
        newUploads.push({
          id: `${file.name}-${Date.now()}`,
          filename: file.name,
          status: "error",
          progress: 0,
          error: "File size exceeds 100MB limit",
        });
        continue;
      }

      newUploads.push({
        id: `${file.name}-${Date.now()}`,
        filename: file.name,
        status: "pending",
        progress: 0,
      });
    }

    setUploads((prev) => [...prev, ...newUploads]);

    // Upload files
    for (const upload of newUploads) {
      if (upload.status !== "pending") continue;

      const file = Array.from(files).find((f) => f.name === upload.filename);
      if (!file) continue;

      try {
        setUploads((prev) => [
          ...prev.map((u) => (u.id === upload.id ? { ...u, status: "uploading", progress: 25 } : u)),
        ]);

        await apiClient.uploadDocument(file);

        setUploads((prev) => [
          ...prev.map((u) => (u.id === upload.id ? { ...u, status: "success", progress: 100 } : u)),
        ]);

        // Remove success after 3 seconds
        setTimeout(() => {
          setUploads((prev) => prev.filter((u) => u.id !== upload.id));
        }, 3000);

        onUploadSuccess?.();
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Upload failed";
        setUploads((prev) => [
          ...prev.map((u) =>
            u.id === upload.id ? { ...u, status: "error", progress: 0, error: errorMessage } : u
          ),
        ]);
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    handleDrag(e);
    if (e.dataTransfer.files) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      processFiles(e.target.files);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full space-y-4">
      {/* Upload Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={triggerFileInput}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
          dragActive
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.csv"
          onChange={handleInputChange}
          className="hidden"
        />

        <Upload className="mx-auto mb-3 text-gray-400" size={40} />
        <p className="text-lg font-semibold text-gray-900 mb-1">Drop files here or click to upload</p>
        <p className="text-sm text-gray-600">Supported formats: PDF, DOCX, TXT, CSV (max 100MB)</p>
      </div>

      {/* Upload Status */}
      {uploads.length > 0 && (
        <div className="bg-white rounded-lg p-4 space-y-3">
          {uploads.map((upload) => (
            <div key={upload.id} className="flex items-start gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  {upload.status === "success" && <CheckCircle className="text-green-600" size={20} />}
                  {upload.status === "error" && <AlertCircle className="text-red-600" size={20} />}
                  {upload.status === "uploading" && <Loader className="text-blue-600 animate-spin" size={20} />}
                  {upload.status === "pending" && <Loader className="text-gray-400" size={20} />}

                  <span className="font-medium text-gray-900">{upload.filename}</span>
                  {upload.status === "success" && <span className="text-xs text-green-600 font-medium">Uploaded</span>}
                </div>

                {upload.status === "error" && upload.error && (
                  <p className="text-sm text-red-600 ml-7">{upload.error}</p>
                )}

                {(upload.status === "uploading" || upload.status === "pending") && (
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2 ml-7">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${upload.progress}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
