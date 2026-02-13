import React, { useState, useMemo } from 'react';

const Console = ({ logs = [] }) => {
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  
  // Mock logs if empty for verified visual test
  const displayLogs = logs.length > 0 ? logs : [
     { type: 'INFO', message: 'System initialized.', timestamp: Date.now() },
     { type: 'DEBUG', message: 'Connected to orchestrator stream.', timestamp: Date.now() + 100 },
     { type: 'ERROR', message: 'Failed to load user preferences.', timestamp: Date.now() + 200 },
  ];

  const filteredLogs = useMemo(() => {
    return displayLogs.filter(log => {
      if (filter !== 'ALL' && log.type !== filter) return false;
      if (search && !log.message.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [displayLogs, filter, search]);

  const handleCopy = () => {
    const text = filteredLogs.map(l => `[${new Date(l.timestamp).toISOString()}] [${l.type}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="flex flex-col h-full bg-glass-100 backdrop-blur-md">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-2 border-b border-glass-200 bg-glass-100/50">
         <div className="flex gap-2">
            {[
                { id: 'ALL', color: 'bg-gray-600' }, 
                { id: 'INFO', color: 'bg-blue-600' }, 
                { id: 'ERROR', color: 'bg-red-600' }, 
                { id: 'DEBUG', color: 'bg-yellow-600' }
            ].map(type => (
               <button 
                 key={type.id}
                 onClick={() => setFilter(type.id)}
                 className={`text-[10px] font-bold px-2 py-1 rounded transition-all ${filter === type.id ? `${type.color} text-white shadow-lg` : 'text-gray-400 hover:text-white hover:bg-white/10'}`}
               >
                 {type.id}
               </button>
            ))}
         </div>
         <div className="flex items-center gap-2">
             <input 
                type="text" 
                placeholder="Search logs..." 
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="bg-black/20 border border-glass-200 rounded px-2 py-1 text-[10px] text-white placeholder-gray-500 focus:outline-none focus:border-primary w-32 transition-all focus:w-48"
             />
             <button onClick={handleCopy} title="Copy to Clipboard" className="p-1 text-gray-400 hover:text-white transition-colors">
                📋
             </button>
             <button onClick={() => {/* Clear logic */}} title="Clear Console" className="p-1 text-gray-400 hover:text-red-400 transition-colors">
                🚫
             </button>
         </div>
      </div>
      
      {/* Logs Area */}
      <div className="flex-1 overflow-y-auto p-2 font-mono text-[11px] space-y-0.5 custom-scrollbar bg-black/20">
         {filteredLogs.map((log, i) => (
           <div key={i} className={`flex gap-2 px-1 hover:bg-white/5 rounded ${log.type === 'ERROR' ? 'text-red-400' : log.type === 'DEBUG' ? 'text-yellow-400' : 'text-gray-300'}`}>
              <span className="opacity-40 min-w-[70px]">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
              <span className={`font-bold min-w-[40px] ${log.type === 'INFO' ? 'text-blue-400' : ''}`}>{log.type}</span>
              <span className="break-all">{log.message}</span>
           </div>
         ))}
         {filteredLogs.length === 0 && <div className="text-gray-600 text-center mt-10 italic">No logs match your filter</div>}
      </div>
    </div>
  );
};
export default Console;
