export interface Document {
  document_id: string;
  metadata: DocumentMetadata;
  chunk_count: number;
  is_indexed: boolean;
}

export interface DocumentMetadata {
  filename: string;
  file_type: string;
  file_size: number;
  upload_date: string;
  num_pages?: number;
  num_chunks: number;
  source_url?: string;
  custom_metadata?: Record<string, any>;
}

export interface SourcePassage {
  document_id: string;
  filename: string;
  content: string;
  chunk_index: number;
  similarity_score: number;
  metadata?: Record<string, any>;
}

export interface SearchResult {
  query: string;
  results: number;
  sources: SourcePassage[];
  retrieval_time_ms: number;
}

export interface GenerationResponse {
  query: string;
  answer: string;
  sources: SourcePassage[];
  model_used: string;
  total_tokens?: number;
}

export interface TextChunk {
  chunk_id: string;
  document_id: string;
  content: string;
  chunk_index: number;
  metadata?: Record<string, any>;
  token_count: number;
}

export interface ChunkVisualization {
  document_id: string;
  filename: string;
  total_chunks: number;
  chunks: TextChunk[];
  chunking_config: ChunkingConfig;
}

export interface ChunkingConfig {
  strategy: string;
  chunk_size: number;
  chunk_overlap: number;
  separator?: string;
}

export interface HealthCheckResponse {
  status: string;
  version: string;
  timestamp: string;
  services: Record<string, string>;
}

export interface ApiError {
  error: string;
  message: string;
  status_code: number;
  timestamp: string;
}

export interface QueryMetrics {
  query: string;
  retrieval_time_ms: number;
  generation_time_ms: number;
  total_time_ms: number;
  num_sources: number;
  tokens_used: number;
}
