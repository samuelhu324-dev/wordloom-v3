import { sendQuickLogEvent } from './quickLogClient';

type CaretIntentKind = 'pointer' | 'keyboard' | 'initial';
type CaretIntentEdge = 'start' | 'end';

export interface BlockEditorCaretIntentTelemetry {
  kind: CaretIntentKind;
  targetId: string | null;
  payload?: {
    edge?: CaretIntentEdge;
    offset?: number;
  };
  source?: string;
}

export const reportBlockEditorCaretIntent = (event: BlockEditorCaretIntentTelemetry) => {
  sendQuickLogEvent({
    type: 'BlockEditorCaretIntent',
    timestamp: Date.now(),
    data: {
      kind: event.kind,
      targetId: event.targetId ?? null,
      edge: event.payload?.edge ?? null,
      offset: typeof event.payload?.offset === 'number' ? event.payload.offset : null,
      source: event.source ?? 'unspecified',
    },
  });
};
