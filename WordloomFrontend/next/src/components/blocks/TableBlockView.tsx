/**
 * TableBlockView - 表格块视图（始终编辑状态）
 */
'use client';

import React, { useState } from 'react';
import { Block, TableBlock } from '@/modules/orbit/domain/blocks';

interface TableBlockViewProps {
  block: Block;
  onUpdate: (block: Block) => void;
}

export function TableBlockView({
  block,
  onUpdate,
}: TableBlockViewProps) {
  const table = block as TableBlock;
  const [rows, setRows] = useState(table.content.rows || [['', ''], ['', '']]);

  const handleSave = () => {
    onUpdate({
      ...block,
      content: {
        ...table.content,
        rows,
      },
      updatedAt: new Date().toISOString(),
    });
  };

  const updateCell = (rowIndex: number, colIndex: number, value: string) => {
    const newRows = rows.map((row, i) =>
      i === rowIndex
        ? row.map((cell, j) => (j === colIndex ? value : cell))
        : row
    );
    setRows(newRows);
    // Trigger auto-save after state update
    setTimeout(() => {
      onUpdate({
        ...block,
        content: {
          ...table.content,
          rows: newRows,
        },
        updatedAt: new Date().toISOString(),
      });
    }, 0);
  };

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse border border-gray-300">
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, colIndex) => (
                  <td key={colIndex} className="border border-gray-300">
                    <input
                      type="text"
                      value={cell}
                      onChange={(e) => updateCell(rowIndex, colIndex, e.target.value)}
                      className="w-full p-3 border-none focus:bg-blue-50 text-gray-900 focus:outline-none"
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => {
            const newRows = [...rows, new Array(rows[0]?.length || 2).fill('')];
            setRows(newRows);
            setTimeout(() => {
              onUpdate({
                ...block,
                content: {
                  ...table.content,
                  rows: newRows,
                },
                updatedAt: new Date().toISOString(),
              });
            }, 0);
          }}
          className="px-3 py-2 bg-gray-300 text-gray-800 text-sm rounded hover:bg-gray-400"
        >
          + 行
        </button>
      </div>
      <div className="flex gap-2 text-xs text-gray-500">
        <span>自动保存（编辑时）</span>
      </div>
    </div>
  );
}
