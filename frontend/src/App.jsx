import React, { useState, useEffect } from 'react';
import EntryField from './components/EntryField';
import ProgressTree from './components/ProgressTree';
import Console from './components/Console';
import Settings from './components/Settings';
import ProcessFlow from './components/ProcessFlow';
import { useSSE } from './hooks/useSSE';
import { useKeyboard } from './hooks/useKeyboard';

function App() {
  const [showSettings, setShowSettings] = useState(false);
  const [config, setConfig] = useState({
    temperature: 70,
    detail: 90,
    context_window: 50,
    verbose: true,
  });
  const [version, setVersion] = useState('...');
  const [clearTrigger, setClearTrigger] = useState(0);

  const { data: sseData, status: sseStatus } = useSSE('/api/stream');

  // Extract data from SSE
  const tasks = sseData?.tasks || [];
  const logs = sseData?.logs || [];
  const processFlow = sseData?.process_flow || null;
  const orchestratorRunning = sseData?.orchestrator_running || false;

  // Set version from SSE init or API
  useEffect(() => {
    if (sseData?.version) {
      setVersion(sseData.version);
    } else {
      fetch('/api/version')
        .then(r => r.json())
        .then(d => setVersion(d.version))
        .catch(() => {});
    }
  }, [sseData?.version]);

  // Sync config from SSE
  useEffect(() => {
    if (sseData?.config) {
      setConfig(prev => ({ ...prev, ...sseData.config }));
    }
  }, [sseData?.config]);

  useKeyboard({
    'Ctrl+,': () => setShowSettings(prev => !prev),
    'Ctrl+K': () => setClearTrigger(t => t + 1),
  });

  const handleSend = (text) => {
    fetch('/api/console', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: text, complexity: 'streamlined' })
    }).catch(console.error);
  };

  const handleConfigChange = (newConfig) => {
    setConfig(newConfig);
    fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newConfig)
    }).catch(console.error);
  };

  const handleReset = () => {
    fetch('/api/reset', { method: 'POST' })
      .then(() => window.location.reload())
      .catch(console.error);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white font-sans overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent/20 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 h-screen flex flex-col p-4 gap-3">
        {/* Header */}
        <header className="flex justify-between items-center p-3 bg-glass-100 backdrop-blur-md rounded-2xl border border-glass-200 shadow-lg">
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
            Hybrid Conductor <span className="text-xs text-gray-400 font-mono">v{version}</span>
          </h1>
          <div className="flex items-center gap-3">
            {/* SSE Status Indicator */}
            <div className="flex items-center gap-1.5" title={`Stream: ${sseStatus}`}>
              <span className={`w-2 h-2 rounded-full ${
                sseStatus === 'connected' ? 'bg-green-400 shadow-[0_0_6px_rgba(74,222,128,0.5)]' :
                sseStatus === 'connecting' ? 'bg-yellow-400 animate-pulse' :
                'bg-red-400'
              }`} />
              <span className="text-[10px] text-gray-500 font-mono">{sseStatus}</span>
            </div>
            {orchestratorRunning && (
              <span className="text-[10px] bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full border border-blue-500/30 animate-pulse">
                Inferencing...
              </span>
            )}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 rounded-lg hover:bg-glass-200 transition-all cursor-pointer"
              aria-label="Settings"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </button>
          </div>
        </header>

        {/* Process Flow Bar */}
        <ProcessFlow data={processFlow} sseStatus={sseStatus} />

        {/* Main Grid */}
        <div className="flex-1 grid grid-cols-12 gap-3 min-h-0">

          {/* Left Panel: Input & Progress */}
          <div className="col-span-12 lg:col-span-7 flex flex-col gap-3 min-h-0">
            <div className="flex-none">
              <EntryField onSend={handleSend} disabled={orchestratorRunning} />
            </div>
            <div className="flex-1 bg-glass-100 backdrop-blur-md rounded-2xl border border-glass-200 overflow-hidden relative">
              <ProgressTree tasks={tasks} />
            </div>
          </div>

          {/* Right Panel: Console */}
          <div className="col-span-12 lg:col-span-5 flex flex-col gap-3 min-h-0">
             <div className="flex-1 bg-glass-100 backdrop-blur-md rounded-2xl border border-glass-200 overflow-hidden relative">
               <Console logs={logs} clearTrigger={clearTrigger} />
             </div>
          </div>
        </div>
      </div>

      {/* Settings Sidebar Overlay */}
      {showSettings && (
        <div className="absolute inset-0 z-50 flex justify-end bg-black/50 backdrop-blur-sm"
             onClick={(e) => { if (e.target === e.currentTarget) setShowSettings(false); }}>
          <div className="w-96 h-full bg-gray-900 border-l border-glass-200 shadow-2xl p-6 overflow-y-auto">
             <Settings
                config={config}
                setConfig={handleConfigChange}
                onReset={handleReset}
                onClose={() => setShowSettings(false)}
                version={version}
             />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
