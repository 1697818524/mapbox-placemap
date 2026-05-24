/**
 * 将地点关键词转为适合作为 data/ingest 目录名的 slug（与后端落盘路径一致）
 */
export function slugifyLocation(raw: string): string {
  const t = raw.trim().slice(0, 120)
  if (!t) return 'default'
  return t
    .replace(/[<>:"/\\|?*\u0000-\u001f]/g, '_')
    .replace(/\s+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '') || 'default'
}
