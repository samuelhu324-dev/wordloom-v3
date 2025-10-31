"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Image from "@tiptap/extension-image";
import Link from "@tiptap/extension-link";
import { uploadImage } from "@/modules/orbit/domain/api";
import { useRef, useState, useEffect } from "react";

export default function RichTextEditor({
  value,
  onChange,
  placeholder = "Write markdown...",
  noteId,
}: {
  value: string;
  onChange: (content: string) => void;
  placeholder?: string;
  noteId?: string;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isMounted, setIsMounted] = useState(false);

  const editor = useEditor(
    {
      extensions: [
        StarterKit.configure({
          heading: { levels: [1, 2, 3] },
          codeBlock: false,
        }),
        Image.configure({
          allowBase64: true,
          HTMLAttributes: {
            class: "max-w-full h-auto rounded",
          },
        }),
        Link.configure({
          openOnClick: false,
          HTMLAttributes: {
            class: "text-blue-600 underline",
          },
        }),
      ],
      content: value || `<p>${placeholder}</p>`,
      onUpdate: ({ editor }) => {
        onChange(editor.getHTML());
      },
      immediatelyRender: false,
    },
    []
  );

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // 外部 value 变化时更新编辑器内容（但只在外部明确改变时）
  useEffect(() => {
    if (editor && value && editor.getHTML() !== value) {
      editor.commands.setContent(value);
    }
  }, [value, editor]);

  const handleImageUpload = async (file: File) => {
    if (!file.type.startsWith("image/")) {
      alert("请选择图片文件");
      return;
    }

    if (!noteId) {
      alert("请先保存 Note");
      return;
    }

    try {
      console.log("上传文件:", file.name, "到 noteId:", noteId);
      const response = await uploadImage(file, noteId);
      console.log("上传响应:", response);
      const imageUrl = response.url;
      console.log("最终 URL:", imageUrl);

      // URL 应该是 /uploads/{noteId}/{filename}
      const finalUrl = imageUrl.startsWith("http") ? imageUrl : imageUrl;

      editor?.chain().focus().setImage({ src: finalUrl }).run();
    } catch (error) {
      console.error("图片上传失败:", error);
      alert("图片上传失败: " + (error as Error).message);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleImageUpload(file);
      e.target.value = "";
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleImageUpload(file);
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLDivElement>) => {
    const file = e.clipboardData.files?.[0];
    if (file && file.type.startsWith("image/")) {
      e.preventDefault();
      handleImageUpload(file);
    }
  };

  if (!isMounted || !editor) {
    return <div className="p-3 border rounded bg-gray-50 text-gray-500">加载编辑器中...</div>;
  }

  return (
    <div className="space-y-2">
      {/* 工具栏 */}
      <div className="flex gap-1 p-2 bg-gray-100 rounded border flex-wrap">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`px-2 py-1 rounded text-sm ${editor.isActive("bold") ? "bg-blue-600 text-white" : "bg-white hover:bg-gray-200"}`}
          title="加粗"
        >
          B
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`px-2 py-1 rounded text-sm ${editor.isActive("italic") ? "bg-blue-600 text-white" : "bg-white hover:bg-gray-200"}`}
          title="斜体"
        >
          I
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={`px-2 py-1 rounded text-sm ${editor.isActive("heading", { level: 2 }) ? "bg-blue-600 text-white" : "bg-white hover:bg-gray-200"}`}
          title="标题"
        >
          H2
        </button>
        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`px-2 py-1 rounded text-sm ${editor.isActive("bulletList") ? "bg-blue-600 text-white" : "bg-white hover:bg-gray-200"}`}
          title="列表"
        >
          •
        </button>
        <div className="border-l mx-1"></div>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="px-2 py-1 rounded text-sm bg-white hover:bg-gray-200"
          title="上传图片"
        >
          🖼️ 图片
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
        />
        <button
          onClick={() => {
            const url = prompt("输入链接地址:");
            if (url) {
              editor.chain().focus().setLink({ href: url }).run();
            }
          }}
          className="px-2 py-1 rounded text-sm bg-white hover:bg-gray-200"
          title="添加链接"
        >
          🔗 链接
        </button>
        <button
          onClick={() => editor.chain().focus().clearContent().run()}
          className="px-2 py-1 rounded text-sm bg-white hover:bg-gray-200 ml-auto"
          title="清空"
        >
          ✕ 清空
        </button>
      </div>

      {/* 编辑器 */}
      <div
        onDrop={handleDrop}
        onPaste={handlePaste}
        onDragOver={(e) => e.preventDefault()}
        suppressHydrationWarning
        className="border rounded p-3 bg-white min-h-48 prose prose-sm max-w-none focus-within:ring-2 focus-within:ring-blue-500 [&_.tiptap]:outline-none [&_img]:max-w-xs [&_img]:h-auto"
      >
        <EditorContent editor={editor} />
      </div>

      {/* 提示 */}
      <p className="text-xs text-gray-500">💡 支持拖拽上传、粘贴图片、点击按钮上传</p>
    </div>
  );
}