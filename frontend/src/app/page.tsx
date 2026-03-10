"use client";

import React, { useState } from "react";
import { FileText, Settings } from "lucide-react";
import QueryInterface from "@/components/QueryInterface";
import DocumentUploader from "@/components/DocumentUploader";

type TabType = "query" | "documents" | "settings";

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>("query");

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
        <div className="p-6 border-b border-gray-700">
          <h1 className="text-2xl font-bold text-white">RAG Engine</h1>
          <p className="text-sm text-gray-400 mt-1">Document Intelligence</p>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          <button
            onClick={() => setActiveTab("query")}
            className={`w-full text-left px-4 py-3 rounded-lg font-medium transition ${
              activeTab === "query"
                ? "bg-blue-600 text-white"
                : "text-gray-300 hover:bg-gray-700"
            }`}
          >
            <span className="flex items-center gap-2">
              <FileText size={20} />
              Query Documents
            </span>
          </button>

          <button
            onClick={() => setActiveTab("documents")}
            className={`w-full text-left px-4 py-3 rounded-lg font-medium transition ${
              activeTab === "documents"
                ? "bg-blue-600 text-white"
                : "text-gray-300 hover:bg-gray-700"
            }`}
          >
            <span className="flex items-center gap-2">
              <FileText size={20} />
              Manage Documents
            </span>
          </button>

          <button
            onClick={() => setActiveTab("settings")}
            className={`w-full text-left px-4 py-3 rounded-lg font-medium transition ${
              activeTab === "settings"
                ? "bg-blue-600 text-white"
                : "text-gray-300 hover:bg-gray-700"
            }`}
          >
            <span className="flex items-center gap-2">
              <Settings size={20} />
              Settings
            </span>
          </button>
        </nav>

        <div className="p-4 border-t border-gray-700 text-xs text-gray-500">
          <p>Version 1.0.0</p>
          <p className="mt-1">
            Built by{" "}
            <a
              href="https://github.com/alrod-dev"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300"
            >
              Alfredo Wiesner
            </a>
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {activeTab === "query" && <QueryInterface />}

        {activeTab === "documents" && <DocumentsPage />}

        {activeTab === "settings" && <SettingsPage />}
      </div>
    </div>
  );
}

function DocumentsPage() {
  const [uploadKey, setUploadKey] = useState(0);

  return (
    <div className="flex flex-col h-full">
      <div className="bg-white border-b border-gray-200 p-6 shadow-sm">
        <h1 className="text-3xl font-bold text-gray-900">Manage Documents</h1>
        <p className="text-gray-600 mt-1">Upload and manage your documents for RAG processing</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto">
          <DocumentUploader
            key={uploadKey}
            onUploadSuccess={() => {
              // Trigger refresh
              setUploadKey((prev) => prev + 1);
            }}
          />
        </div>
      </div>
    </div>
  );
}

function SettingsPage() {
  const [selectedTab, setSelectedTab] = useState("chunking");

  return (
    <div className="flex flex-col h-full">
      <div className="bg-white border-b border-gray-200 p-6 shadow-sm">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Configure RAG engine parameters</p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-6">
          <div className="mb-6 border-b border-gray-200">
            <div className="flex gap-4">
              <button
                onClick={() => setSelectedTab("chunking")}
                className={`px-4 py-3 font-medium transition ${
                  selectedTab === "chunking"
                    ? "border-b-2 border-blue-600 text-blue-600"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                Chunking Config
              </button>
            </div>
          </div>

          {selectedTab === "chunking" && (
            <div className="max-w-2xl">
              {/* Import ConfigPanel here */}
              <div className="bg-white rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Chunking Configuration</h3>
                <p className="text-gray-600">Configure document chunking parameters</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
