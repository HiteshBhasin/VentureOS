'use client';

import { useEffect, useState, useCallback } from 'react';
import { TaskFile } from '@/types/task';
import { getTaskFiles, getTaskFile } from '@/lib/api';

interface ProjectViewerProps {
  taskId: string;
}

export function ProjectViewer({ taskId }: ProjectViewerProps): React.JSX.Element | null {
  const [files, setFiles] = useState<TaskFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reportContent, setReportContent] = useState<string | null>(null);
  const [openFile, setOpenFile] = useState<string | null>(null);
  const [fileContents, setFileContents] = useState<Record<string, string>>({});
  const [loadingFile, setLoadingFile] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await getTaskFiles(taskId);
        if (cancelled) return;
        setFiles(list);
        if (list.some((f) => f.path === 'report.md')) {
          const report = await getTaskFile(taskId, 'report.md');
          if (!cancelled) setReportContent(report.content);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load project output');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [taskId]);

  const toggleFile = useCallback(
    async (path: string) => {
      if (openFile === path) {
        setOpenFile(null);
        return;
      }
      setOpenFile(path);
      if (fileContents[path] === undefined) {
        setLoadingFile(path);
        try {
          const data = await getTaskFile(taskId, path);
          setFileContents((prev) => ({ ...prev, [path]: data.content }));
        } catch {
          setFileContents((prev) => ({ ...prev, [path]: '(failed to load file)' }));
        } finally {
          setLoadingFile(null);
        }
      }
    },
    [taskId, openFile, fileContents]
  );

  if (loading) {
    return (
      <div className="text-[10px] text-zinc-600 tracking-widest uppercase">Loading project output...</div>
    );
  }
  if (error || files.length === 0) {
    return null;
  }

  const codeFiles = files.filter((f) => f.path !== 'report.md' && f.path !== 'results.json');

  return (
    <div className="flex flex-col gap-3 max-w-2xl">
      {reportContent && (
        <div className="rounded border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="text-[9px] text-zinc-600 tracking-widest uppercase mb-2">Report</div>
          <pre className="text-[11px] text-zinc-300 whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto font-sans">
            {reportContent}
          </pre>
        </div>
      )}

      {codeFiles.length > 0 && (
        <div className="rounded border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="text-[9px] text-zinc-600 tracking-widest uppercase mb-2">
            Generated Files ({codeFiles.length})
          </div>
          <div className="flex flex-col gap-1.5">
            {codeFiles.map((f) => (
              <div key={f.path} className="border border-zinc-800 rounded overflow-hidden">
                <button
                  onClick={() => toggleFile(f.path)}
                  className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-zinc-800/50 transition-colors"
                >
                  <span className="text-[10px] text-cyan-400 font-mono truncate">{f.path}</span>
                  <span className="text-[9px] text-zinc-600 shrink-0 ml-2">{f.size_bytes}B</span>
                </button>
                {openFile === f.path && (
                  <pre className="text-[10px] text-zinc-400 whitespace-pre-wrap p-3 border-t border-zinc-800 max-h-64 overflow-y-auto bg-black/20">
                    {loadingFile === f.path ? 'Loading...' : fileContents[f.path]}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
