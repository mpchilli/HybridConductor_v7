import React, { useState, useRef, useEffect, useMemo } from 'react';

const Console = ({ logs = [], clearTrigger = 0 }) => {
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [cleared, setCleared] = useState([]);
  const bottomRef = useRef(null);

  // Clear logs when trigger changes
  useEffect(() => {
    if (clearTrigger > 0) setCleared([...logs]);
  }, [clearTrigger]);

  // Filter out cleared logs
  const activeLogs = logs.filter(l => !cleared.includes(l));

  // No mock data — show real state. If empty, show waiting message.
  const displayLogs = activeLogs.length > 0 ? activeLogs : [];

  const filteredLogs = useMemo(() => {
    return displayLogs.filter(log => {
      if (filter !== 'ALL' && log.type !== filter) return false;
      if (search && !log.message.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [displayLogs, filter, search]);

  // Auto-scroll to bottom on new logs
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredLogs.length]);

  const handleCopy = () => {
    const text = filteredLogs.map(l => `[${new Date(l.timestamp).toISOString()}] [${l.type}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(text);
  };

  const logTypes = [
    { id: 'ALL', color: 'bg-gray-600' },
    { id: 'INFO', color: 'bg-blue-600' },
    { id: 'ERROR', color: 'bg-red-600' },
    { id: 'WARN', color: 'bg-amber-600' },
    { id: 'DEBUG', color: 'bg-yellow-600' },
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-2 border-b border-glass-200 bg-glass-100/50">
         <div className="flex gap-1">
            {logTypes.map(type => (
               <button
                 key={type.id}
                 onClick={() => setFilter(type.id)}
                 className={`text-[10px] font-bold px-2 py-1 rounded transition-all cursor-pointer ${filter === type.id ? `${type.color} text-white shadow-lg` : 'text-gray-400 hover:text-white hover:bg-white/10'}`}
               >
                 {type.id}
               </button>
            ))}
         </div>
         <div className="flex items-center gap-2">
             <input
                type="text"
                placeholder="Search..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="bg-black/20 border border-glass-200 rounded px-2 py-1 text-[10px] text-white placeholder-gray-500 focus:outline-none focus:border-primary w-24 transition-all focus:w-40"
             />
             <button onClick={handleCopy} title="Copy to Clipboard" className="p-1 text-gray-400 hover:text-white transition-colors cursor-pointer">
               <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
             </button>
             <span className="text-[9px] text-gray-600 font-mono">{filteredLogs.length}</span>
         </div>
      </div>

      {/* Logs Area */}
      <div className="flex-1 overflow-y-auto p-2 font-mono text-[11px] space-y-0.5 custom-scrollbar bg-black/20">
         {filteredLogs.length === 0 && (
           <div className="text-gray-600 text-center mt-10 italic text-xs">
             {displayLogs.length === 0 ? 'Waiting for orchestrator output...' : 'No logs match your filter'}
           </div>
         )}
         {filteredLogs.map((log, i) => (
           <div key={i} className={`flex gap-2 px-1 hover:bg-white/5 rounded ${
             log.type === 'ERROR' ? 'text-red-400' :
             log.type === 'WARN' ? 'text-amber-400' :
             log.type === 'DEBUG' ? 'text-yellow-400' :
             'text-gray-300'
           }`}>
              <span className="opacity-40 min-w-[70px] flex-shrink-0">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
              <span className={`font-bold min-w-[40px] flex-shrink-0 ${log.type === 'INFO' ? 'text-blue-400' : ''}`}>{log.type}</span>
              <span className="break-all">{log.message}</span>
           </div>
         ))}
         <div ref={bottomRef} />
      </div>
    </div>
  );
};

export default Console;
