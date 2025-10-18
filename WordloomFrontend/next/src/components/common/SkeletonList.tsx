"use client";
import React from "react";

type Props = { rows?: number };

export default function SkeletonList({ rows = 8 }: Props) {
  return (
    <ul className="divide-y divide-gray-200">
      {Array.from({ length: rows }).map((_, i) => (
        <li key={i} className="py-3">
          <div className="animate-pulse space-y-2">
            <div className="h-4 w-3/5 rounded bg-gray-200" />
            <div className="h-3 w-4/5 rounded bg-gray-100" />
          </div>
        </li>
      ))}
    </ul>
  );
}
