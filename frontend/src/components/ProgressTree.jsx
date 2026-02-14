import React, { useState } from 'react';

const ProgressTree = ({ tasks = [] }) => {
  // No mock data — show real state
  if (tasks.length === 0) {
    return (
      <div className="h-full flex flex-col p-4">
        <div className="sticky top-0 bg-glass-100/90 backdrop-blur-md pb-2 mb-2 z-10 border-b border-glass-200">
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
            Thinking Chains
            <span className="ml-auto text-xs bg-glass-200 px-2 py-0.5 rounded text-white font-mono">0</span>
          </h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-600 text-sm italic">No active thinking chains. Submit a task to begin.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-4 overflow-y-auto custom-scrollbar">
      <div className="sticky top-0 bg-glass-100/90 backdrop-blur-md pb-2 mb-2 z-10 border-b border-glass-200">
        <h2 className="text-sm font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
           Thinking Chains
           <span className="ml-auto text-xs bg-glass-200 px-2 py-0.5 rounded text-white font-mono">{tasks.length}</span>
        </h2>
      </div>
      <div className="space-y-2">
        {tasks.map(task => (
            <TaskNode key={task.id} task={task} />
        ))}
      </div>
    </div>
  );
};

const TaskNode = ({ task }) => {
    const [expanded, setExpanded] = useState(true);

    const statusConfig = {
        pending: { style: 'bg-gray-800/50 border-gray-700 text-gray-400', icon: '○', dot: 'bg-gray-600' },
        running: { style: 'bg-blue-900/20 border-blue-500/30 text-blue-300 shadow-[0_0_10px_rgba(59,130,246,0.1)]', icon: '●', dot: 'bg-blue-400 animate-pulse' },
        completed: { style: 'bg-emerald-900/20 border-emerald-500/30 text-emerald-300', icon: '✓', dot: 'bg-emerald-400' },
        failed: { style: 'bg-red-900/20 border-red-500/30 text-red-300', icon: '✕', dot: 'bg-red-400' },
    };

    const config = statusConfig[task.status] || statusConfig.pending;

    return (
        <div className="relative pl-6 before:content-[''] before:absolute before:left-[11px] before:top-0 before:bottom-0 before:w-px before:bg-glass-200 last:before:bottom-auto last:before:h-1/2">

            {/* Connector Line */}
            <div className="absolute left-[11px] top-1/2 w-3 h-px bg-glass-200 -translate-y-1/2" />

            <div
                className={`group p-3 rounded-lg border backdrop-blur-sm cursor-pointer transition-all hover:bg-glass-200 hover:scale-[1.01] active:scale-[0.99] ${config.style}`}
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex justify-between items-center gap-3">
                    <div className="flex items-center gap-2 overflow-hidden">
                        <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${config.dot}`} />
                        <span className="font-medium font-mono text-sm truncate">{task.name}</span>
                    </div>

                    {task.children?.length > 0 && (
                        <span className={`text-[10px] text-gray-500 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}>
                            ▼
                        </span>
                    )}
                </div>

                {/* Micro-details on hover */}
                {task.details && (
                    <div className="hidden group-hover:block mt-2 pt-2 border-t border-white/5 text-xs text-gray-400 font-mono">
                        {task.details}
                    </div>
                )}
            </div>

            {expanded && task.children && (
                <div className="mt-2 pr-1">
                    {task.children.map(child => <TaskNode key={child.id} task={child} />)}
                </div>
            )}
        </div>
    );
};

export default ProgressTree;
