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
  is_demo: boolean;
  portfolio_id: number;
  created_at: string;
  updated_at: string;
}

export interface DemoSeedResult {
  portfolio_id: number;
  connections: Array<{
    id: number;
    label: string;
    platform: string;
    status: SyncStatus;
    positions_synced: number;
    transactions_synced: number;
  }>;
  positions_synced: number;
  transactions_synced: number;
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

export async function getDemoFeaturesEnabled(): Promise<boolean> {
  const response = await api.get<ApiEnvelope<{ enabled: boolean }>>(
    "integrations/demo/status/",
  );
  return response.data.data.enabled;
}

export async function seedDemoPortfolio(): Promise<DemoSeedResult> {
  const response = await api.post<ApiEnvelope<DemoSeedResult>>(
    "integrations/demo/seed/",
  );
  return response.data.data;
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
