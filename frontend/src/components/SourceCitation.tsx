"use client";

import React, { useState } from "react";
import { ChevronDown } from "lucide-react";
import { SourcePassage } from "@/types";

interface SourceCitationProps {
  source: SourcePassage;
  index: number;
}

export default function SourceCitation({ source, index }: SourceCitationProps) {
  const [expanded, setExpanded] = useState(false);

  const truncatedContent = source.content.length > 150 ? source.content.substring(0, 150) + "..." : source.content;

  const relevanceColor =
    source.similarity_score > 0.7 ? "bg-green-100 text-green-800" : source.similarity_score > 0.4 ? "bg-yellow-100 text-yellow-800" : "bg-gray-100 text-gray-800";

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start justify-between text-left"
      >
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-block w-6 h-6 bg-blue-600 text-white text-xs font-bold rounded-full text-center leading-6">
              {index}
            </span>
            <h4 className="font-semibold text-gray-900">{source.filename}</h4>
            <span className={`text-xs font-semibold px-2 py-1 rounded ${relevanceColor}`}>
              {(source.similarity_score * 100).toFixed(0)}% relevant
            </span>
          </div>
          <p className="text-sm text-gray-600 line-clamp-2">{truncatedContent}</p>
        </div>

        <ChevronDown
          size={20}
          className={`text-gray-400 flex-shrink-0 ml-2 transition-transform ${expanded ? "transform rotate-180" : ""}`}
        />
      </button>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="bg-gray-50 p-3 rounded text-sm text-gray-800 leading-relaxed max-h-64 overflow-y-auto">
            {source.content}
          </div>
          <div className="mt-3 flex items-center gap-4 text-xs text-gray-600">
            <span>Chunk: {source.chunk_index}</span>
            <span>Score: {source.similarity_score.toFixed(3)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
