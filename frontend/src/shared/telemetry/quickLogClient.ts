const QUICKLOG_ENDPOINT = '/api/quicklog';

export interface QuickLogEnvelope {
  type: string;
  timestamp: number;
  data: Record<string, unknown>;
}

const postWithFetch = (body: string) => {
  void fetch(QUICKLOG_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body,
    keepalive: true,
  }).catch(() => {
    // 网络问题导致的失败无需抛出，让调用方继续。
  });
};

export const sendQuickLogEvent = (envelope: QuickLogEnvelope) => {
  if (typeof window === 'undefined') {
    // SSR 或测试环境无法透传时，记录到服务器日志，避免静默丢弃。
    if (typeof console !== 'undefined' && typeof console.info === 'function') {
      console.info('[QuickLog]', envelope.type, envelope);
    }
    return;
  }

  const body = JSON.stringify(envelope);
  if (navigator?.sendBeacon) {
    const blob = new Blob([body], { type: 'application/json' });
    const sent = navigator.sendBeacon(QUICKLOG_ENDPOINT, blob);
    if (!sent) {
      postWithFetch(body);
    }
    return;
  }
  postWithFetch(body);
};
