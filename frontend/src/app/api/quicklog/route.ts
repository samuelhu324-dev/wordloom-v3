import { NextResponse } from 'next/server';

interface QuickLogRequestBody {
  type?: string;
  timestamp?: number;
  data?: Record<string, unknown>;
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as QuickLogRequestBody;
    if (!body?.type) {
      return NextResponse.json({ ok: false, error: 'missing type' }, { status: 400 });
    }
    console.info('[QuickLog::api]', body.type, body);
    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error('[QuickLog::api] invalid payload', error);
    return NextResponse.json({ ok: false, error: 'invalid json' }, { status: 400 });
  }
}
