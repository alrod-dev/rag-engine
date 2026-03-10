"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Loader, AlertCircle } from "lucide-react";
import { apiClient } from "@/lib/api";
import { GenerationResponse, SourcePassage } from "@/types";
import SourceCitation from "./SourceCitation";

export default function QueryInterface() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<SourcePassage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [topK, setTopK] = useState(5);
  const [useHybrid, setUseHybrid] = useState(true);
  const [streaming, setStreaming] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [answer]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      setError("Please enter a query");
      return;
    }

    setLoading(true);
    setError("");
    setAnswer("");
    setSources([]);

    try {
      if (streaming) {
        // Streaming approach
        let fullAnswer = "";

        for await (const chunk of apiClient.generateWithStreaming(query, topK, useHybrid)) {
          try {
            const parsed = JSON.parse(chunk);

            if (parsed.chunk) {
              fullAnswer += parsed.chunk;
              setAnswer(fullAnswer);
            }

            if (parsed.sources) {
              setSources(parsed.sources);
            }

            if (parsed.error) {
              setError(parsed.error);
            }
          } catch {
            // Ignore parsing errors for non-JSON chunks
          }
        }
      } else {
        // Non-streaming approach
        const response = await apiClient.generate(query, topK, useHybrid);

        setAnswer(response.answer);
        setSources(response.sources);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate answer");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-blue-50 to-indigo-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6 shadow-sm">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Document Intelligence RAG</h1>
        <p className="text-gray-600">Ask questions about your uploaded documents</p>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Answer Display */}
        {answer && (
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{answer}</p>
            </div>
          </div>
        )}

        {/* Sources */}
        {sources.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Sources</h3>
            <div className="space-y-3">
              {sources.map((source, idx) => (
                <SourceCitation key={idx} source={source} index={idx + 1} />
              ))}
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="text-red-600 mt-0.5 flex-shrink-0" size={20} />
            <div>
              <h4 className="font-semibold text-red-900">Error</h4>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {loading && !answer && (
          <div className="flex items-center justify-center gap-3 py-8">
            <Loader className="animate-spin text-blue-600" size={24} />
            <span className="text-gray-600 font-medium">Generating answer...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Search Form */}
      <div className="bg-white border-t border-gray-200 p-6 shadow-lg">
        <form onSubmit={handleSearch} className="space-y-4">
          {/* Options */}
          <div className="flex flex-wrap gap-4 items-center text-sm">
            <div className="flex items-center gap-2">
              <label className="text-gray-700 font-medium">Top K:</label>
              <input
                type="number"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
                className="w-16 px-2 py-1 border border-gray-300 rounded"
              />
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useHybrid}
                onChange={(e) => setUseHybrid(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-gray-700">Hybrid Search</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={streaming}
                onChange={(e) => setStreaming(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-gray-700">Streaming</span>
            </label>
          </div>

          {/* Query Input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about your documents..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition flex items-center gap-2"
            >
              {loading ? <Loader className="animate-spin" size={20} /> : <Send size={20} />}
              Search
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
