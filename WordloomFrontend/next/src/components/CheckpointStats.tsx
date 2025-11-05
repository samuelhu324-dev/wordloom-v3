/**
 * CheckpointStats - 检查点统计和可视化组件
 */
'use client';

import React from 'react';
import { CheckpointDetail, formatDuration } from '@/modules/orbit/domain/checkpoints';
import { TrendingUp, Clock, Pause, Zap } from 'lucide-react';

interface CheckpointStatsProps {
  checkpoint: CheckpointDetail;
}

/**
 * 时间统计展示组件 - Hover 浮窗版本
 */
export function CheckpointStats({ checkpoint }: CheckpointStatsProps) {
  const workDuration = checkpoint.duration_seconds;
  const completion = checkpoint.completion_percentage;
  const markerCount = checkpoint.markers.length;

  return (
    <div className="relative group">
      {/* Hover 触发区域 - 显示统计图标 */}
      <div className="flex items-center gap-2 text-xs text-gray-500 cursor-help">
        <Zap className="w-4 h-4" />
        <TrendingUp className="w-4 h-4" />
      </div>

      {/* Hover 浮窗 - 显示详细信息 */}
      <div className="absolute right-0 top-full mt-1 p-3 bg-white rounded-lg border border-gray-200 shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 w-64 whitespace-normal">
        {/* 工作时长 */}
        <div className="flex items-center justify-between mb-3 pb-3 border-b border-gray-200">
          <div className="flex items-center gap-2 text-sm">
            <Zap className="w-4 h-4 text-blue-600" />
            <span className="font-medium text-gray-700">工作时长</span>
          </div>
          <span className="font-bold text-blue-900">{formatDuration(workDuration)}</span>
        </div>

        {/* 完成度 */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-purple-600" />
              <span className="font-medium text-gray-700">完成度</span>
            </div>
            <span className="font-bold text-purple-900">{Math.round(completion)}%</span>
          </div>
          <div className="w-full h-2 bg-purple-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
              style={{ width: `${completion}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 多个检查点的统计对比
 */
interface CheckpointsComparison {
  checkpoints: CheckpointDetail[];
}

export function CheckpointsComparison({
  checkpoints,
}: CheckpointsComparison) {
  if (checkpoints.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        暂无检查点数据
      </div>
    );
  }

  const totalWorkTime = checkpoints.reduce(
    (sum, c) => sum + c.duration_seconds,
    0
  );
  const averageCompletion =
    checkpoints.reduce((sum, c) => sum + c.completion_percentage, 0) /
    checkpoints.length;

  return (
    <div className="space-y-3">
      <h4 className="font-semibold text-sm text-gray-900">整体统计</h4>

      <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
        <p className="text-xs text-blue-600 font-medium">总工作时长</p>
        <p className="text-lg font-bold text-blue-900">
          {formatDuration(totalWorkTime)}
        </p>
      </div>

      <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
        <p className="text-xs text-purple-600 font-medium">平均完成度</p>
        <p className="text-lg font-bold text-purple-900">
          {Math.round(averageCompletion)}%
        </p>
      </div>

      {/* 检查点列表 */}
      <div className="space-y-2">
        {checkpoints.map((checkpoint) => (
          <div
            key={checkpoint.id}
            className="p-2 bg-gray-50 rounded border border-gray-200 text-xs"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-medium truncate">{checkpoint.title}</span>
              <span className="text-gray-600">
                {formatDuration(checkpoint.duration_seconds)}
              </span>
            </div>
            <div className="w-full h-1.5 bg-gray-300 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
                style={{
                  width: `${Math.min(
                    (checkpoint.duration_seconds / Math.max(totalWorkTime, 1)) *
                      100,
                    100
                  )}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
