import { api } from "./api";

interface ApiEnvelope<T> {
  data: T;
  error: string | null;
  message: string;
}

export type SyncStatus = "pending" | "running" | "success" | "error";

export interface PlatformConnection {
  id: number;
  platform: string;
  platform_display: string;
  connection_method: string;
  connection_method_display: string;
  label: string;
  display_name: string;
  status: SyncStatus;
  last_synced_at: string | null;
  last_error: string;
  is_active: boolean;
  portfolio_id: number;
  created_at: string;
  updated_at: string;
}

export interface SyncJob {
  id: number;
  connection_id: number;
  status: SyncStatus;
  positions_synced: number;
  transactions_synced: number;
  error_message: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface BitvavoConnectPayload {
  api_key: string;
  api_secret: string;
  label?: string;
}

export interface BitvavoConnectResponse extends PlatformConnection {
  sync_job?: SyncJob;
}

export async function listConnections(): Promise<PlatformConnection[]> {
  const response = await api.get<ApiEnvelope<PlatformConnection[]>>(
    "integrations/connections/",
  );
  return response.data.data;
}

export async function connectBitvavo(
  payload: BitvavoConnectPayload,
): Promise<BitvavoConnectResponse> {
  const response = await api.post<ApiEnvelope<BitvavoConnectResponse>>(
    "integrations/connections/bitvavo/",
    payload,
  );
  return response.data.data;
}

export async function deleteConnection(connectionId: number): Promise<void> {
  await api.delete(`integrations/connections/${connectionId}/`);
}

export async function triggerSync(connectionId: number): Promise<SyncJob> {
  const response = await api.post<ApiEnvelope<SyncJob>>(
    `integrations/connections/${connectionId}/sync/`,
  );
  return response.data.data;
}

export async function getSyncJob(jobId: number): Promise<SyncJob> {
  const response = await api.get<ApiEnvelope<SyncJob>>(
    `integrations/sync-jobs/${jobId}/`,
  );
  return response.data.data;
}

export interface CsvSkippedRowReport {
  line_number: number;
  reason: string;
  description: string;
  preview: string;
}

export interface CsvImportResult {
  platform: string;
  platform_display: string;
  connection_id: number;
  rows_in_file: number;
  rows_recognized: number;
  rows_parsed: number;
  transactions_imported: number;
  transactions_skipped: number;
  rows_skipped_unrecognized: number;
  rows_skipped_other: number;
  skipped_rows: CsvSkippedRowReport[];
  skipped_rows_truncated: boolean;
  unknown_descriptions: string[];
  has_import_gaps: boolean;
  trust_summary: string;
  by_type?: Record<string, number>;
  detection?: {
    confidence: number;
    missing_headers: string[];
  };
}

/** @deprecated Gebruik CsvImportResult */
export interface CsvDetectionMatch {
  platform: string;
  platform_display: string;
  confidence: number;
  missing_headers: string[];
}

export interface CsvPreviewTransaction {
  date: string;
  time: string;
  transaction_type: string;
  symbol: string;
  name: string;
  quantity: string | null;
  price_eur: string | null;
  fee_eur: string | null;
  total_eur: string | null;
  status: "new" | "duplicate";
  transaction_hash: string;
}

export interface CsvPreviewIssue {
  line_number: number;
  reason: string;
  description: string;
  preview: string;
  suggestion: string;
}

export interface CsvPreviewSummary {
  rows_in_file: number;
  rows_recognized: number;
  new: number;
  duplicate: number;
  skipped_unrecognized: number;
  skipped_other: number;
  transactions_truncated: boolean;
  transactions_total: number;
}

export type CsvPreviewFailureReason =
  | "unsupported_platform"
  | "platform_mismatch"
  | "no_recognized_rows"
  | "parse_error";

export interface CsvSchemaWarning {
  code: string;
  severity: "info" | "warning";
  message: string;
  file_header?: string;
  canonical?: string;
}

export interface CsvSuggestedAlias {
  file_header: string;
  canonical: string;
  canonical_label: string;
  matched_alias: string;
  confidence: number;
}

export interface CsvColumnSchemaReport {
  schema_version: string;
  mapped_columns: Record<string, string>;
  missing_required: string[];
  unmapped_headers: string[];
  schema_warnings: CsvSchemaWarning[];
  suggested_aliases: CsvSuggestedAlias[];
  has_blocking_issues: boolean;
  has_warnings: boolean;
}

/** Hoe kolommen gekoppeld zijn: schema (normaal), fuzzy, of AI-fallback. */
export interface CsvColumnMappingReport {
  source: string;
  mapped_columns: Record<string, string>;
  missing_required: string[];
  suggested_aliases: CsvSuggestedAlias[];
  maintenance_snippets: string[];
  ai_used: boolean;
  parser_ready: boolean;
  ai_available: boolean;
}

export interface CsvPreviewResult {
  status: "ok" | "rejected";
  failure_reason: CsvPreviewFailureReason | null;
  message: string | null;
  platform?: string;
  platform_display?: string;
  file_headers: string[];
  detection?: CsvImportResult["detection"];
  matches: CsvDetectionMatch[];
  supported_platforms: { platform: string; display_name: string }[];
  summary: CsvPreviewSummary | null;
  transactions: CsvPreviewTransaction[];
  issues: CsvPreviewIssue[];
  unknown_descriptions: string[];
  has_import_gaps: boolean;
  has_schema_warnings?: boolean;
  column_schema?: CsvColumnSchemaReport | null;
  column_mapping?: CsvColumnMappingReport;
  can_confirm_import: boolean;
  confirm_hint: string;
}

export async function previewPlatformCsv(
  file: File,
  options?: { platform?: string },
): Promise<CsvPreviewResult> {
  const formData = new FormData();
  formData.append("file", file);
  if (options?.platform) {
    formData.append("platform", options.platform);
  }
  const response = await api.post<ApiEnvelope<CsvPreviewResult>>(
    "integrations/csv/preview/",
    formData,
    { headers: { "Content-Type": false as unknown as string } },
  );
  return response.data.data;
}

export async function detectCsvPlatform(file: File): Promise<{
  matches: CsvDetectionMatch[];
  recommended: string | null;
}> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<
    ApiEnvelope<{ matches: CsvDetectionMatch[]; recommended: string | null }>
  >("integrations/csv/detect/", formData, {
    headers: { "Content-Type": false as unknown as string },
  });
  return response.data.data;
}

export async function importPlatformCsv(
  file: File,
  options?: { platform?: string; label?: string },
): Promise<CsvImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  if (options?.platform) {
    formData.append("platform", options.platform);
  }
  if (options?.label) {
    formData.append("label", options.label);
  }

  const response = await api.post<ApiEnvelope<CsvImportResult>>(
    "integrations/csv/import/",
    formData,
    {
      headers: { "Content-Type": false as unknown as string },
    },
  );
  return response.data.data;
}

export async function pollSyncJob(
  jobId: number,
  options?: { intervalMs?: number; maxAttempts?: number },
): Promise<SyncJob> {
  const intervalMs = options?.intervalMs ?? 1500;
  const maxAttempts = options?.maxAttempts ?? 40;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const job = await getSyncJob(jobId);
    if (job.status === "success" || job.status === "error") {
      return job;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  return getSyncJob(jobId);
}
