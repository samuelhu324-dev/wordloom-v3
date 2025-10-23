// next/src/app/orbit/page.tsx
'use client';

import { useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';

import type { Task, TaskStatus, TaskPriority, TaskDomain, Memo } from '@/modules/orbit/domain/types';
import { listTasks, createTask, deleteTask, updateTask } from '@/modules/orbit/services/tasks';
import { listMemos, createMemo } from '@/modules/orbit/services/memos';

const STATUS: TaskStatus[] = ['todo','doing','done','archived'];
const PRIORITY: TaskPriority[] = ['low','normal','high','urgent'];
const DOMAIN: TaskDomain[] = ['dev','translate','research','study'];

export default function OrbitPage() {
  const [view, setView] = useState<'tasks' | 'memos'>('tasks');

  // ---------- Tasks ----------
  const [tasks, setTasks] = useState<Task[]>([]);
  const [qTask, setQTask] = useState('');
  const [status, setStatus] = useState<TaskStatus | ''>('');
  const [priority, setPriority] = useState<TaskPriority | ''>('');
  const [domain, setDomain] = useState<TaskDomain | ''>('');
  const [newTitle, setNewTitle] = useState('');

  // ---------- Memos ----------
  const [memos, setMemos] = useState<Memo[]>([]);
  const [qMemo, setQMemo] = useState('');
  const [newMemo, setNewMemo] = useState('');

  // ---------- Common ----------
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ kind: 'info'|'error', text: string } | null>(null);

  function toast(kind: 'info'|'error', text: string, ms = 2200) {
    setMsg({ kind, text });
    if (ms > 0) setTimeout(() => setMsg(null), ms);
  }

  async function refresh() {
    setLoading(true);
    try {
      if (view === 'tasks') {
        const res = await listTasks({
          q: qTask,
          status: status || undefined,
          priority: priority || undefined,
          domain: domain || undefined,
          order_by: 'created_at',
          order: 'desc',
        });
        setTasks(res);
      } else {
        const res = await listMemos({ q: qMemo, order_by: 'created_at', order: 'desc' });
        setMemos(res);
      }
    } catch (e: any) {
      toast('error', e.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [view]);

  // ---------- Task actions ----------
  async function handleAddTask() {
    if (!newTitle.trim()) return;
    try {
      const t = await createTask({ title: newTitle });
      setTasks(prev => [t, ...prev]);
      setNewTitle('');
      toast('info', 'Task created');
    } catch (e: any) {
      toast('error', e.message);
    }
  }

  async function handleDeleteTask(id: number) {
    try {
      await deleteTask(id);
      setTasks(prev => prev.filter(t => t.id !== id));
      toast('info', 'Task deleted');
    } catch (e: any) {
      toast('error', e.message);
    }
  }

  // ---------- Memo actions ----------
  async function handleAddMemo() {
    if (!newMemo.trim()) return;
    try {
      const memo = await createMemo({ text: newMemo });
      setMemos(prev => [memo, ...prev]);
      setNewMemo('');
      toast('info', 'Memo created');
    } catch (e: any) {
      toast('error', e.message);
    }
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

      {/* Message bar */}
      {msg && (
        <div className={`rounded-md px-3 py-2 text-sm ${msg.kind === 'error' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}>
          {msg.text}
        </div>
      )}

      {/* Search / Filters */}
      {view === 'tasks' ? (
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <Input
              placeholder="Search tasks..."
              value={qTask}
              onChange={(e) => setQTask(e.target.value)}
              className="flex-1"
            />
            <Button onClick={refresh} disabled={loading}>Search</Button>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Select value={status} onValueChange={(v) => setStatus(v as TaskStatus | '')} placeholder="Status">
              <option value="">All Status</option>
              {STATUS.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>

            <Select value={priority} onValueChange={(v) => setPriority(v as TaskPriority | '')} placeholder="Priority">
              <option value="">All Priority</option>
              {PRIORITY.map(p => <option key={p} value={p}>{p}</option>)}
            </Select>

            <Select value={domain} onValueChange={(v) => setDomain(v as TaskDomain | '')} placeholder="Domain">
              <option value="">All Domain</option>
              {DOMAIN.map(d => <option key={d} value={d}>{d}</option>)}
            </Select>

            <Button variant="outline" onClick={() => { setStatus(''); setPriority(''); setDomain(''); setQTask(''); }}>Reset</Button>
          </div>
        </section>
      ) : (
        <section className="flex items-center gap-2">
          <Input
            placeholder="Search memos..."
            value={qMemo}
            onChange={(e) => setQMemo(e.target.value)}
            className="flex-1"
          />
          <Button onClick={refresh} disabled={loading}>Search</Button>
        </section>
      )}

      {/* Content */}
      {view === 'tasks' && (
        <section>
          <div className="flex items-center gap-2 mt-4">
            <Input
              placeholder="Quick add a new task"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddTask()}
              className="flex-1"
            />
            <Button onClick={handleAddTask}>Add</Button>
          </div>

          {loading && <p className="mt-4 text-gray-500">Loading...</p>}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-6">
            {tasks.map(task => (
              <Card key={task.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <h3 className="font-semibold">{task.title}</h3>
                  <p className="text-sm text-gray-500">{task.note ?? '—'}</p>
                  <div className="flex justify-between items-center mt-3 text-xs text-gray-400">
                    <span>{task.status} · {task.priority} · {task.domain}</span>
                    <Button size="sm" variant="ghost" onClick={() => handleDeleteTask(task.id)}>Delete</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}

      {view === 'memos' && (
        <section>
          <div className="flex items-center gap-2 mt-4">
            <Input
              placeholder="Quick add a memo"
              value={newMemo}
              onChange={(e) => setNewMemo(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddMemo()}
              className="flex-1"
            />
            <Button onClick={handleAddMemo}>Add</Button>
          </div>

          {loading && <p className="mt-4 text-gray-500">Loading...</p>}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-6">
            {memos.map(m => (
              <Card key={m.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <p className="text-sm">{m.text}</p>
                  <div className="flex justify-between items-center mt-3 text-xs text-gray-400">
                    <span>{m.tags ?? '—'}</span>
                    {/* 预留删除/编辑入口，后续批次接入 */}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
