// next/src/app/orbit/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import type { Task, Memo } from '@/modules/orbit/domain/types';
import { listTasks, createTask } from '@/modules/orbit/services/tasks';
import { listMemos, createMemo } from '@/modules/orbit/services/memos';

export default function OrbitPage() {
  const [view, setView] = useState<'tasks' | 'memos'>('tasks');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [memos, setMemos] = useState<Memo[]>([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState('');
  const [newMemo, setNewMemo] = useState('');

  async function refresh() {
    setLoading(true);
    try {
      if (view === 'tasks') {
        const res = await listTasks({});
        setTasks(res);
      } else {
        const res = await listMemos({});
        setMemos(res);
      }
    } catch (e: any) {
      setMsg(e.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, [view]);

  async function handleAddTask() {
    if (!newTitle.trim()) return;
    const t = await createTask({ title: newTitle });
    setTasks(prev => [t, ...prev]);
    setNewTitle('');
  }

  async function handleAddMemo() {
    if (!newMemo.trim()) return;
    const m = await createMemo({ text: newMemo });
    setMemos(prev => [m, ...prev]);
    setNewMemo('');
  }

  return (
    <div className="p-6 space-y-6">
      <header className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Orbit</h1>
        <div className="space-x-2">
          <Button variant={view === 'tasks' ? 'default' : 'outline'} onClick={() => setView('tasks')}>Tasks</Button>
          <Button variant={view === 'memos' ? 'default' : 'outline'} onClick={() => setView('memos')}>Memos</Button>
        </div>
      </header>
      {msg && <div className="text-red-600 text-sm">{msg}</div>}
      {view === 'tasks' ? (
        <section>
          <div className="flex items-center gap-2 mt-4">
            <Input placeholder="Quick add a new task" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} />
            <Button onClick={handleAddTask}>Add</Button>
          </div>
          {loading && <p className="mt-4 text-gray-500">Loading...</p>}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-6">
            {tasks.map(t => (
              <Card key={t.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <h3 className="font-semibold">{t.title}</h3>
                  <p className="text-sm text-gray-500">{t.note ?? '—'}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      ) : (
        <section>
          <div className="flex items-center gap-2 mt-4">
            <Input placeholder="Quick add a memo" value={newMemo} onChange={(e) => setNewMemo(e.target.value)} />
            <Button onClick={handleAddMemo}>Add</Button>
          </div>
          {loading && <p className="mt-4 text-gray-500">Loading...</p>}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-6">
            {memos.map(m => (
              <Card key={m.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <p className="text-sm">{m.text}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
