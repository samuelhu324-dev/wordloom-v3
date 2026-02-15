import { sendQuickLogEvent } from './quickLogClient';
import { afterNextPaint, createCorrelationId, nowMs } from './correlationId';

export type UiRequestHandle = {
  correlationId: string;
  operation: string;
  tClickMs: number;
  tResponseMs?: number;
};

export const startUiRequest = (operation: string, correlationId?: string): UiRequestHandle => {
  return {
    correlationId: correlationId || createCorrelationId(),
    operation,
    tClickMs: nowMs(),
  };
};

export const markUiResponse = (handle: UiRequestHandle): UiRequestHandle => {
  return {
    ...handle,
    tResponseMs: nowMs(),
  };
};

export const emitUiRendered = async (handle: UiRequestHandle, extra?: Record<string, unknown>) => {
  await afterNextPaint();
  const tRenderedMs = nowMs();

  sendQuickLogEvent({
    type: 'ui.request',
    timestamp: Date.now(),
    data: {
      correlation_id: handle.correlationId,
      operation: handle.operation,
      t_click_ms: handle.tClickMs,
      t_response_ms: handle.tResponseMs,
      t_rendered_ms: tRenderedMs,
      d_network_ms: handle.tResponseMs ? handle.tResponseMs - handle.tClickMs : undefined,
      d_render_ms: handle.tResponseMs ? tRenderedMs - handle.tResponseMs : undefined,
      d_total_ms: tRenderedMs - handle.tClickMs,
      ...extra,
    },
  });
};
