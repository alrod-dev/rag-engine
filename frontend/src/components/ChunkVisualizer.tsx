"use client";

import React, { useState, useEffect } from "react";
import { Loader, AlertCircle } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Document } from "@/types";

interface ChunkVisualizerProps {
  document: Document;
}

export default function ChunkVisualizer({ document }: ChunkVisualizerProps) {
  const [expanded, setExpanded] = useState(false);
  const [chunks, setChunks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadChunks = async () => {
    if (chunks.length > 0) {
      setExpanded(!expanded);
      return;
    }

    setLoading(true);
    setError("");

    try {
      // This would require an endpoint to get chunk details
      // For now, we'll show a placeholder
      setChunks([
        {
          chunk_id: "1",
          content: "Sample chunk content...",
          token_count: 50,
        },
      ]);
      setExpanded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load chunks");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <button
        onClick={loadChunks}
        className="w-full flex items-center justify-between text-left font-semibold text-gray-900 hover:text-blue-600 transition"
      >
        <span>
          {document.metadata.filename} ({document.chunk_count} chunks)
        </span>
        {loading && <Loader className="animate-spin text-blue-600" size={20} />}
      </button>

      {error && (
        <div className="mt-2 flex items-center gap-2 text-red-600 text-sm">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-2 max-h-96 overflow-y-auto">
          {chunks.map((chunk) => (
            <div key={chunk.chunk_id} className="bg-gray-50 p-3 rounded text-sm">
              <p className="font-mono text-xs text-gray-600 mb-1">Chunk {chunk.chunk_id}</p>
              <p className="text-gray-700 line-clamp-3">{chunk.content}</p>
              <p className="mt-2 text-xs text-gray-500">{chunk.token_count} tokens</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
