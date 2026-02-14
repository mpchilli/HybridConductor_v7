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
  const notifications = sseData?.notifications || { discord: false, telegram: 'disabled' };

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
            {/* Notification Status */}
            <div className="flex items-center gap-2 border-r border-glass-200 pr-3 mr-1">
               {/* Discord */}
               <div className={`p-1.5 rounded-md transition-colors ${notifications?.discord ? 'text-[#5865F2] bg-[#5865F2]/10' : 'text-gray-600'}`} title={notifications?.discord ? "Discord Connected" : "Discord Disabled"}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037 14.12 14.12 0 0 0-.624 1.282 18.257 18.257 0 0 0-5.457 0 14.125 14.125 0 0 0-.627-1.282.074.074 0 0 0-.079-.037 19.795 19.795 0 0 0-4.887 1.515.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.076.076 0 0 0-.04.106 13.682 13.682 0 0 0 1.225 1.994.077.077 0 0 0 .084.028 19.897 19.897 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.074.074 0 0 0-.031-.028zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>
               </div>
               {/* Telegram */}
               <div className={`p-1.5 rounded-md transition-colors ${
                  notifications?.telegram === 'connected' ? 'text-[#24A1DE] bg-[#24A1DE]/10' : 
                  notifications?.telegram_error ? 'text-red-400 bg-red-400/10 animate-pulse' : 
                  notifications?.telegram === 'connecting' ? 'text-yellow-400 bg-yellow-400/10 animate-pulse' :
                  'text-gray-600'
               }`} title={`Telegram: ${notifications?.telegram || 'disabled'}`}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
               </div>
            </div>

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
