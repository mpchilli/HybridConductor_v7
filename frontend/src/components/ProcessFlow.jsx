import React from 'react';

/**
 * ProcessFlow - Mermaid-style process flow visualization
 *
 * Shows: Planning → Building → Verifying → Complete
 * - Green: completed stages
 * - Blue pulse: current active stage
 * - Grey: pending stages
 * - Red: failed stage
 * - Qty badge: stages visited more than once
 * - Error banner if backend not providing data
 * - History log with timestamps for debugging
 */
const ProcessFlow = ({ data, sseStatus }) => {
  const stages = ['planning', 'building', 'verifying', 'complete'];
  const stageLabels = {
    planning: 'Planning',
    building: 'Building',
    verifying: 'Verifying',
    complete: 'Complete',
  };

  const hasData = data && data.stages;
  const hasError = data?.error;
  const currentStage = data?.current_stage;
  const history = data?.history || [];

  if (!hasData && sseStatus === 'error') {
    return (
      <div className="bg-red-900/20 border border-red-500/30 rounded-2xl p-3">
        <div className="flex items-center gap-2 text-red-400 text-sm font-medium">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
          Backend disconnected — no process flow data available
        </div>
      </div>
    );
  }

  return (
    <div className="bg-glass-100 backdrop-blur-md rounded-2xl border border-glass-200 p-3">
      {/* Flow Diagram */}
      <div className="flex items-center justify-between gap-1">
        {stages.map((stage, i) => {
          const stageData = hasData ? data.stages[stage] : null;
          const count = stageData?.count || 0;
          const isCompleted = stageData?.completed || false;
          const isCurrent = currentStage === stage;
          const isFailed = currentStage === 'failed' && stage === stages[stages.indexOf(currentStage)] ;

          // Determine style
          let bgClass = 'bg-gray-800/50 border-gray-700 text-gray-500';
          let dotClass = 'bg-gray-600';

          if (isCompleted) {
            bgClass = 'bg-emerald-900/30 border-emerald-500/40 text-emerald-300';
            dotClass = 'bg-emerald-400';
          }
          if (isCurrent && !isCompleted) {
            bgClass = 'bg-blue-900/30 border-blue-500/40 text-blue-300 shadow-[0_0_12px_rgba(59,130,246,0.15)]';
            dotClass = 'bg-blue-400 animate-pulse';
          }
          if (currentStage === 'failed' && !isCompleted && count === 0) {
            // Leave as grey
          }

          return (
            <React.Fragment key={stage}>
              {/* Node */}
              <div className={`relative flex-1 flex items-center gap-2 px-3 py-2 rounded-xl border transition-all ${bgClass}`}>
                <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${dotClass}`} />
                <span className="text-xs font-medium font-mono truncate">{stageLabels[stage]}</span>
                {count > 1 && (
                  <span className="absolute -top-1.5 -right-1.5 bg-amber-500 text-black text-[9px] font-bold w-4 h-4 rounded-full flex items-center justify-center shadow">
                    {count}
                  </span>
                )}
              </div>
              {/* Arrow connector */}
              {i < stages.length - 1 && (
                <svg width="20" height="12" viewBox="0 0 20 12" className="flex-shrink-0 text-gray-600">
                  <path d="M0 6 L14 6 M10 2 L16 6 L10 10" stroke="currentColor" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
            </React.Fragment>
          );
        })}

        {/* Failed indicator */}
        {currentStage === 'failed' && (
          <>
            <svg width="20" height="12" viewBox="0 0 20 12" className="flex-shrink-0 text-red-500">
              <path d="M0 6 L14 6 M10 2 L16 6 L10 10" stroke="currentColor" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <div className="flex-1 flex items-center gap-2 px-3 py-2 rounded-xl border bg-red-900/30 border-red-500/40 text-red-300">
              <span className="w-2.5 h-2.5 rounded-full bg-red-400 flex-shrink-0" />
              <span className="text-xs font-medium font-mono">Failed</span>
            </div>
          </>
        )}
      </div>

      {/* Error Banner */}
      {hasError && (
        <div className="mt-2 px-3 py-1.5 bg-red-900/20 border border-red-500/20 rounded-lg text-red-400 text-[11px] font-mono">
          Error: {data.error}
        </div>
      )}

      {/* History Log (collapsible) */}
      {history.length > 0 && (
        <details className="mt-2">
          <summary className="text-[10px] text-gray-500 cursor-pointer hover:text-gray-300 transition-colors font-mono">
            History ({history.length} events)
          </summary>
          <div className="mt-1 max-h-24 overflow-y-auto custom-scrollbar space-y-0.5 text-[10px] font-mono">
            {history.slice(-20).reverse().map((h, i) => (
              <div key={i} className="flex gap-2 text-gray-500 px-1">
                <span className="opacity-60 min-w-[140px]">{new Date(h.timestamp).toLocaleTimeString()}</span>
                <span className={`min-w-[70px] ${
                  h.event === 'error' ? 'text-red-400' :
                  h.event === 'completed' ? 'text-emerald-400' : 'text-blue-400'
                }`}>{h.event}</span>
                <span>{h.stage}</span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
};

export default ProcessFlow;
