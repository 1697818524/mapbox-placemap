/**
 * Pipeline 任务 API（与后端 /api/pipeline 对齐）
 */
import { API_CONFIG, getApiBaseUrl } from '@/config'
import type { ColorSchemeWithId } from '@/api/scheme'

const backendBase = () => getApiBaseUrl()

function abortAfter(ms: number): AbortSignal {
  const c = new AbortController()
  setTimeout(() => c.abort(), ms)
  return c.signal
}

export type PipelineJobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled'

export interface PipelineOptions {
  enable_shadow?: boolean
  enable_semantic?: boolean
  enable_superpixel?: boolean
  enable_cluster?: boolean
  enable_scheme?: boolean
  semantic_model?: string
  slic_n_segments?: number
  slic_compactness?: number
  cluster_k_min?: number
  cluster_k_max?: number
  scheme_count?: number
  /** 使用 NSGA-II（和谐度 + 地方表征性），需 cluster CSV */
  enable_ga_scheme?: boolean
  ga_population?: number
  ga_generations?: number
  scheme_background_semantic?: string
}

export interface PipelineJobCreateRequest {
  location: string
  image_ids: string[]
  options?: PipelineOptions
}

export interface PipelineJobCreateResponse {
  job_id: string
  status: PipelineJobStatus
  message?: string
}

export interface PipelineStageProgress {
  stage: string
  status: PipelineJobStatus
  progress: number
  started_at?: string | null
  finished_at?: string | null
  message?: string | null
}

export interface PipelineSchemesResponse {
  job_id: string
  schemes: ColorSchemeWithId[]
}

export interface PipelinePaletteSemanticsResponse {
  job_id: string
  semantics: string[]
}

export interface PipelineJob {
  job_id: string
  status: PipelineJobStatus
  location: string
  image_ids: string[]
  options: Required<PipelineOptions>
  current_stage?: string | null
  progress: number
  stages: PipelineStageProgress[]
  error_code?: string | null
  error_message?: string | null
  created_at: string
  updated_at: string
  started_at?: string | null
  finished_at?: string | null
  /** GET /jobs/{id} 附加：cluster 目录下 palette_*.csv 数量 */
  palette_csv_count?: number
}

async function parseError(res: Response): Promise<string> {
  try {
    const j = await res.json()
    if (j?.detail?.message) return j.detail.message
    if (typeof j?.detail === 'string') return j.detail
  } catch {
    /* ignore */
  }
  return res.statusText
}

/** 是否允许基于当前任务调用「生成方案」（开启聚类时需已有 palette_*.csv 候选） */
export function isSchemeGenerationReady(job: PipelineJob): boolean {
  if (job.status !== 'succeeded') return false
  if (job.options.enable_cluster) {
    return (job.palette_csv_count ?? 0) > 0
  }
  return true
}

export const pipelineApi = {
  async createJob(payload: PipelineJobCreateRequest): Promise<PipelineJobCreateResponse> {
    const res = await fetch(`${backendBase()}/api/pipeline/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: abortAfter(API_CONFIG.TIMEOUT),
    })
    if (!res.ok) throw new Error(await parseError(res))
    return res.json()
  },

  async getJob(jobId: string): Promise<PipelineJob> {
    const res = await fetch(`${backendBase()}/api/pipeline/jobs/${encodeURIComponent(jobId)}`, {
      signal: abortAfter(API_CONFIG.TIMEOUT),
    })
    if (!res.ok) throw new Error(await parseError(res))
    return res.json()
  },

  /** 读取任务目录下已生成的 scheme JSON（与 POST /schemes/generate 结构一致） */
  async getJobSchemes(jobId: string): Promise<PipelineSchemesResponse> {
    const res = await fetch(
      `${backendBase()}/api/pipeline/jobs/${encodeURIComponent(jobId)}/schemes`,
      { signal: abortAfter(API_CONFIG.TIMEOUT) },
    )
    if (!res.ok) throw new Error(await parseError(res))
    return res.json()
  },

  /** 异步执行，返回 202 与当前任务快照 */
  async getJobPaletteSemantics(jobId: string): Promise<PipelinePaletteSemanticsResponse> {
    const res = await fetch(
      `${backendBase()}/api/pipeline/jobs/${encodeURIComponent(jobId)}/palette-semantics`,
      { signal: abortAfter(API_CONFIG.TIMEOUT) },
    )
    if (!res.ok) throw new Error(await parseError(res))
    return res.json()
  },

  async runJob(jobId: string): Promise<PipelineJob> {
    const res = await fetch(`${backendBase()}/api/pipeline/jobs/${encodeURIComponent(jobId)}/run`, {
      method: 'POST',
      signal: abortAfter(API_CONFIG.TIMEOUT),
    })
    if (!res.ok) throw new Error(await parseError(res))
    return res.json()
  },

  /** 同步阻塞直至完成 */
  async runJobSync(jobId: string): Promise<PipelineJob> {
    const res = await fetch(`${backendBase()}/api/pipeline/jobs/${encodeURIComponent(jobId)}/run-sync`, {
      method: 'POST',
      signal: abortAfter(API_CONFIG.TIMEOUT * 120),
    })
    if (!res.ok) throw new Error(await parseError(res))
    return res.json()
  },

  /** 轮询直到结束或超时 */
  async waitForTerminal(
    jobId: string,
    opts: {
      intervalMs?: number
      timeoutMs?: number
      onProgress?: (job: PipelineJob) => void
    } = {},
  ): Promise<PipelineJob> {
    const intervalMs = opts.intervalMs ?? 1500
    const timeoutMs = opts.timeoutMs ?? 30 * 60 * 1000
    const onProgress = opts.onProgress
    const start = Date.now()
    for (;;) {
      const job = await this.getJob(jobId)
      onProgress?.(job)
      if (job.status === 'succeeded' || job.status === 'failed' || job.status === 'cancelled') {
        return job
      }
      if (Date.now() - start > timeoutMs) {
        throw new Error('等待 pipeline 超时')
      }
      await new Promise(r => setTimeout(r, intervalMs))
    }
  },
}
