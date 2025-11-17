'use client';

import React, { useState } from 'react';
import { useLibraries, useCreateLibrary, useDeleteLibrary } from '@/features/library';
import { config } from '@/shared/lib/config';
import { LibraryDto } from '@/entities/library';
import styles from './libraries.module.css';

// Mock libraries for development/testing
const MOCK_LIBRARIES: LibraryDto[] = [
  {
    id: 'test-123',
    name: '我的书库',
    description: '这是一个测试书库，包含我收藏的所有书籍',
    user_id: 'user-1',
    created_at: '2025-11-01T10:00:00Z',
    updated_at: '2025-11-16T10:00:00Z',
  },
  {
    id: 'demo-456',
    name: '团队知识库',
    description: '团队共享的学习和项目文档',
    user_id: 'user-1',
    created_at: '2025-10-20T09:30:00Z',
    updated_at: '2025-11-10T09:30:00Z',
  },
];

export default function LibrariesPage() {
  const useMock = config.flags.useMock;

  const {
    data: realLibraries = [],
    isLoading: isRealLoading,
    error: realError,
  } = useMock ? ({} as any) : useLibraries();

  const libraries: LibraryDto[] = useMock ? MOCK_LIBRARIES : (realLibraries as LibraryDto[]);
  const isLoading = useMock ? false : isRealLoading;
  const error = useMock ? null : (realError as any);
  const createMutation = useCreateLibrary();
  const deleteMutation = useDeleteLibrary();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('latest');
  const [formData, setFormData] = useState({ name: '', description: '' });

  const filteredLibraries = (libraries || []).filter((lib: LibraryDto) =>
    lib.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (lib.description && lib.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleCreateLibrary = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    try {
      await createMutation.mutateAsync({
        name: formData.name,
        description: formData.description,
      });
      setFormData({ name: '', description: '' });
      setIsFormOpen(false);
    } catch (err) {
      console.error('Failed to create library:', err);
    }
  };

  const handleDeleteLibrary = async (id: string) => {
    if (confirm('确定要删除这个库吗？')) {
      try {
        await deleteMutation.mutateAsync(id);
      } catch (err) {
        console.error('Failed to delete library:', err);
      }
    }
  };

  const handleSelectLibrary = (id: string) => {
    console.log('Navigate to library:', id);
    // TODO: Navigate to library detail page
  };

  return (
    <main className={styles.container}>
      {/* Header Section */}
      <div className={styles.header}>
        <div className={styles.headerTitle}>
          <h1>📚 我的书架</h1>
          <p>整理和管理你的 Notes</p>
        </div>
        <button
          className={styles.createButton}
          onClick={() => setIsFormOpen(true)}
          disabled={createMutation.isPending}
        >
          + 新建书架
        </button>
      </div>

      {/* Search and Filter Section */}
      <div className={styles.controls}>
        <div className={styles.searchBox}>
          <input
            type="text"
            placeholder="搜索书架..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={styles.searchInput}
          />
          <span className={styles.searchIcon}>🔍</span>
        </div>

        <div className={styles.filterControls}>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className={styles.select}
          >
            <option value="latest">最新创建</option>
            <option value="name">按名称</option>
            <option value="updated">最近更新</option>
          </select>

          <div className={styles.viewToggle}>
            <button className={styles.viewButton + ' ' + styles.active}>
              📋
            </button>
            <button className={styles.viewButton}>
              ⋮
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className={styles.errorMessage}>
          ⚠️ 加载库失败: {error instanceof Error ? error.message : '未知错误'}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className={styles.loadingState}>
          <div className={styles.spinner} />
          <p>加载中...</p>
        </div>
      )}

      {/* Libraries Grid */}
      {!isLoading && (
        <div className={styles.librariesGrid}>
          {filteredLibraries && filteredLibraries.length > 0 ? (
            filteredLibraries.map((library: LibraryDto) => (
              <div
                key={library.id}
                className={styles.libraryCard}
                onClick={() => handleSelectLibrary(library.id)}
              >
                {/* Card Cover */}
                <div
                  className={styles.cardCover}
                  style={{
                    backgroundColor: generateColorFromId(library.id),
                  }}
                >
                  {/* Overlay with gradient */}
                  <div className={styles.cardOverlay} />

                  {/* Card Title - positioned on cover */}
                  <div className={styles.cardTitleOverlay}>
                    <h3>{library.name}</h3>
                    {library.description && <p>{library.description}</p>}
                  </div>

                  {/* Delete Button */}
                  <button
                    className={styles.deleteButton}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteLibrary(library.id);
                    }}
                    disabled={deleteMutation.isPending}
                    title="删除"
                  >
                    ✕
                  </button>
                </div>

                {/* Card Footer - Stats */}
                <div className={styles.cardFooter}>
                  <span className={styles.stat}>
                    📖 本书架
                  </span>
                  <span className={styles.stat}>
                    ⏰ {new Date(library.created_at || '').toLocaleDateString('zh-CN')}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className={styles.emptyState}>
              <p>📭 还没有创建任何书架</p>
              <button
                className={styles.emptyCreateButton}
                onClick={() => setIsFormOpen(true)}
              >
                创建第一个书架
              </button>
            </div>
          )}
        </div>
      )}

      {/* Create Library Modal */}
      {isFormOpen && (
        <div className={styles.modal} onClick={() => setIsFormOpen(false)}>
          <div
            className={styles.modalContent}
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.modalHeader}>
              <h2>创建新书架</h2>
              <button
                className={styles.modalCloseButton}
                onClick={() => setIsFormOpen(false)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateLibrary}>
              <div className={styles.formGroup}>
                <label htmlFor="name">书架名称 *</label>
                <input
                  id="name"
                  type="text"
                  placeholder="输入书架名称"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className={styles.input}
                  required
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="description">描述</label>
                <textarea
                  id="description"
                  placeholder="输入书架描述（可选）"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className={styles.textarea}
                  rows={4}
                />
              </div>

              <div className={styles.modalButtons}>
                <button
                  type="button"
                  className={styles.cancelButton}
                  onClick={() => setIsFormOpen(false)}
                  disabled={createMutation.isPending}
                >
                  取消
                </button>
                <button
                  type="submit"
                  className={styles.submitButton}
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? '创建中...' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}

// Helper function to generate consistent colors
function generateColorFromId(id: string): string {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1',
    '#FFA07A', '#98D8C8', '#F7DC6F',
    '#BB8FCE', '#85C1E2', '#F8B88B',
  ];
  const hash = id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return colors[hash % colors.length];
}