"use client";

import React, { useState, useEffect } from "react";
import { Save, Loader, AlertCircle } from "lucide-react";
import { apiClient } from "@/lib/api";
import { ChunkingConfig } from "@/types";

export default function ConfigPanel() {
  const [config, setConfig] = useState<ChunkingConfig>({
    strategy: "recursive",
    chunk_size: 512,
    chunk_overlap: 100,
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const currentConfig = await apiClient.getChunkingConfig();
      setConfig(currentConfig);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load config");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    setMessage("");

    try {
      await apiClient.updateChunkingConfig(config);
      setMessage("Configuration updated successfully");

      setTimeout(() => setMessage(""), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save config");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-6">
        <Loader className="animate-spin text-blue-600 mr-2" size={20} />
        <span className="text-gray-600">Loading configuration...</span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Chunking Configuration</h3>

        {/* Strategy */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Strategy</label>
          <select
            value={config.strategy}
            onChange={(e) => setConfig({ ...config, strategy: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="fixed">Fixed Size</option>
            <option value="recursive">Recursive</option>
            <option value="semantic">Semantic</option>
          </select>
          <p className="mt-1 text-sm text-gray-500">
            {config.strategy === "fixed" && "Fixed-size chunks with overlap"}
            {config.strategy === "recursive" && "Recursive splitting using natural separators"}
            {config.strategy === "semantic" && "Chunk based on semantic sentence boundaries"}
          </p>
        </div>

        {/* Chunk Size */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Chunk Size: {config.chunk_size} characters
          </label>
          <input
            type="range"
            min="128"
            max="2048"
            step="64"
            value={config.chunk_size}
            onChange={(e) => setConfig({ ...config, chunk_size: parseInt(e.target.value) })}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <p className="mt-1 text-sm text-gray-500">Larger chunks capture more context but fewer results</p>
        </div>

        {/* Chunk Overlap */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Chunk Overlap: {config.chunk_overlap} characters
          </label>
          <input
            type="range"
            min="0"
            max={Math.max(config.chunk_size - 64, 100)}
            step="10"
            value={config.chunk_overlap}
            onChange={(e) => setConfig({ ...config, chunk_overlap: parseInt(e.target.value) })}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <p className="mt-1 text-sm text-gray-500">Overlap ensures context continuity between chunks</p>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {message && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">{message}</div>
      )}

      {/* Save Button */}
      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition flex items-center justify-center gap-2"
      >
        {saving ? <Loader className="animate-spin" size={20} /> : <Save size={20} />}
        {saving ? "Saving..." : "Save Configuration"}
      </button>
    </div>
  );
}
