import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    console.log('[Upload API] 收到上传请求');

    const formData = await request.formData();
    const file = formData.get('file') as File;

    if (!file) {
      console.error('[Upload API] 没有文件');
      return NextResponse.json(
        { error: '没有选择文件' },
        { status: 400 }
      );
    }

    console.log('[Upload API] 文件信息:', { name: file.name, type: file.type, size: file.size });

    // 验证是否为图片
    if (!file.type.startsWith('image/')) {
      console.error('[Upload API] 不是图片类型:', file.type);
      return NextResponse.json(
        { error: '只支持图片文件' },
        { status: 400 }
      );
    }

    // 生成唯一文件名
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(7);
    const ext = file.type.split('/')[1] || 'png';
    const fileName = `img_${timestamp}_${random}.${ext}`;

    console.log('[Upload API] 生成文件名:', fileName);

    // 保存路径（相对于 public 目录）
    const uploadDir = join(process.cwd(), 'public', 'uploads');
    const filePath = join(uploadDir, fileName);

    console.log('[Upload API] 上传目录:', uploadDir);
    console.log('[Upload API] 文件路径:', filePath);

    // 确保上传目录存在
    try {
      await mkdir(uploadDir, { recursive: true });
      console.log('[Upload API] 上传目录已创建/存在');
    } catch (err) {
      console.error('[Upload API] 创建目录失败:', err);
      throw err;
    }

    // 将文件转换为 Buffer 并保存
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    console.log('[Upload API] 文件大小:', buffer.length, 'bytes');

    await writeFile(filePath, buffer);
    console.log('[Upload API] 文件已保存');

    // 返回可访问的 URL
    const url = `/uploads/${fileName}`;

    console.log('[Upload API] 返回 URL:', url);

    return NextResponse.json({ url }, { status: 200 });
  } catch (error) {
    console.error('[Upload API] 错误:', error);
    const errorMessage = error instanceof Error ? error.message : '未知错误';
    return NextResponse.json(
      { error: '文件上传失败', details: errorMessage },
      { status: 500 }
    );
  }
}
