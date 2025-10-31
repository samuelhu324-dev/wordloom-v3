/**
 * Orbit Diagrams API - 结构图生成
 */

import { apiFetch } from "@/lib/api";
import { ORBIT_BASE } from "@/lib/apiBase";

const DIAGRAMS_BASE = `${ORBIT_BASE}/notes`;

export interface DiagramResponse {
  mermaid_code: string;
  status: string;
}

/**
 * 为 Note 生成 Mermaid 结构图
 * @param noteId Note ID
 * @param chartType 图表类型：auto | flowchart | mindmap | timeline | stateDiagram
 */
export async function generateDiagram(
  noteId: string,
  chartType: string = "auto"
): Promise<DiagramResponse> {
  return apiFetch<DiagramResponse>(`${DIAGRAMS_BASE}/${noteId}/generate-diagram`, {
    method: "POST",
    body: { chart_type: chartType } as any,
  });
}
