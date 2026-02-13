import React, { useState } from 'react';
import EntryField from './components/EntryField';
import ProgressTree from './components/ProgressTree';
import Console from './components/Console';
import Settings from './components/Settings';
import { useSSE } from './hooks/useSSE';
import { useKeyboard } from './hooks/useKeyboard';

function App() {
  const [showSettings, setShowSettings] = useState(false);
  const { data: sseData, status: sseStatus } = useSSE('/api/stream');
  
  // Use SSE data or fallback to defaults
  const tasks = sseData?.tasks || [];
  const logs = sseData?.logs || [];

  useKeyboard({
    'Ctrl+,': () => setShowSettings(prev => !prev),
    'Ctrl+K': () => console.log('Clear console triggered'), // Console clears usually internal state
  });

  const handleSend = (text) => {
    fetch('/api/console', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: text })
    }).catch(console.error);
  };


  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white font-sans overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent/20 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 h-screen flex flex-col p-4 gap-4">
        {/* Header */}
        <header className="flex justify-between items-center p-4 bg-glass-100 backdrop-blur-md rounded-2xl border border-glass-200 shadow-lg">
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
            Ralph Orchestrator <span className="text-xs text-gray-400 font-mono">v8.0</span>
          </h1>
          <button 
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 rounded-lg hover:bg-glass-200 transition-all"
            aria-label="Settings"
          >
            ⚙️
          </button>
        </header>

        {/* Main Grid */}
        <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
          
          {/* Left Panel: Input & Progress */}
          <div className="col-span-12 lg:col-span-8 flex flex-col gap-4 min-h-0">
            {/* Entry Field */}
            <div className="flex-none">
              <EntryField onSend={handleSend} />
            </div>
            
            {/* Progress Tree */}
            <div className="flex-1 bg-glass-100 backdrop-blur-md rounded-2xl border border-glass-200 overflow-hidden relative">
              <ProgressTree tasks={tasks} />
            </div>
          </div>

          {/* Right Panel: Console & Details */}
          <div className="col-span-12 lg:col-span-4 flex flex-col gap-4 min-h-0">
             <div className="flex-1 bg-glass-100 backdrop-blur-md rounded-2xl border border-glass-200 overflow-hidden relative">
               <Console logs={logs} />
             </div>
          </div>
        </div>
      </div>

      {/* Settings Sidebar Overlay */}
      {showSettings && (
        <div className="absolute inset-0 z-50 flex justify-end bg-black/50 backdrop-blur-sm">
          <div className="w-96 h-full bg-gray-900 border-l border-glass-200 shadow-2xl p-6 overflow-y-auto">
             <Settings onClose={() => setShowSettings(false)} />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
