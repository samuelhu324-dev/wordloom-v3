'use client';
export function InlineEditor({ entry, onSave, onClose }) {
  const [zh, setZh] = useState(entry.text_zh);
  const [en, setEn] = useState(entry.text_en);

  return (
    <div className="p-3 border-t border-gray-200 bg-white rounded-md shadow-inner mt-2">
      <textarea
        className="w-full p-2 border rounded text-sm mb-2"
        value={en}
        onChange={(e) => setEn(e.target.value)}
      />
      <textarea
        className="w-full p-2 border rounded text-sm mb-2"
        value={zh}
        onChange={(e) => setZh(e.target.value)}
      />
      <div className="flex justify-end gap-2">
        <button onClick={onClose} className="text-gray-500 text-sm">取消</button>
        <button
          onClick={() => onSave({ ...entry, text_en: en, text_zh: zh })}
          className="bg-blue-500 text-white px-3 py-1 rounded text-sm"
        >
          保存
        </button>
      </div>
    </div>
  );
}
