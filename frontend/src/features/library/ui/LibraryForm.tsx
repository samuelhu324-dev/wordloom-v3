'use client';

import React, { useState } from 'react';
import { CreateLibraryRequest } from '@/entities/library';
import { Button, Input, Modal } from '@/shared/ui';

export interface LibraryFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateLibraryRequest) => void;
  isLoading?: boolean;
}

export const LibraryForm: React.FC<LibraryFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    onSubmit({ name, description: description || undefined });
    setName('');
    setDescription('');
  };

  return (
    <Modal isOpen={isOpen} title="Create Library" onClose={onClose}>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
        <Input
          label="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter library name"
          required
        />
        <Input
          label="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Enter description (optional)"
        />
        <div style={{ display: 'flex', gap: 'var(--spacing-md)', justifyContent: 'flex-end' }}>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={isLoading}>
            Create
          </Button>
        </div>
      </form>
    </Modal>
  );
};
