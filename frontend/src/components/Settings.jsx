import React from 'react';

const Settings = ({ config, setConfig, onReset, onClose, version }) => {
  const updateConfig = (key, value) => {
    const newConfig = { ...config, [key]: typeof config[key] === 'boolean' ? value : parseInt(value) };
    setConfig(newConfig);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">Settings</h2>
        <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors cursor-pointer">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <div className="space-y-8 flex-1 overflow-y-auto custom-scrollbar pr-2">
        {/* LLM Parameters */}
        <div>
            <h3 className="text-xs font-bold text-gray-500 mb-4 uppercase tracking-widest border-b border-gray-800 pb-1">LLM Parameters</h3>
            <div className="space-y-6">
                <Slider
                    label="Temperature"
                    value={config.temperature}
                    onChange={(v) => updateConfig('temperature', v)}
                    color="accent"
                    hint="Controls randomness of AI output (0 = deterministic, 100 = creative)"
                />
                <Slider
                    label="Detail Level"
                    value={config.detail}
                    onChange={(v) => updateConfig('detail', v)}
                    color="primary"
                    hint="Depth of output generation"
                />
                <Slider
                    label="Context Window"
                    value={config.context_window}
                    onChange={(v) => updateConfig('context_window', v)}
                    color="blue"
                    hint="Amount of context fed to the model"
                />
            </div>
        </div>

        {/* Observability */}
        <div>
          <h3 className="text-xs font-bold text-gray-500 mb-4 uppercase tracking-widest border-b border-gray-800 pb-1">Observability</h3>
          <Toggle
            label="Verbose Logging"
            checked={config.verbose}
            onChange={(v) => updateConfig('verbose', v)}
            hint="Stream every system action to console"
          />
        </div>

        {/* Shortcuts Section */}
        <div>
            <h3 className="text-xs font-bold text-gray-500 mb-4 uppercase tracking-widest border-b border-gray-800 pb-1">Keyboard Shortcuts</h3>
            <div className="space-y-2 text-sm text-gray-300">
                <Shortcut label="Run Task" keys={['Ctrl', 'Enter']} />
                <Shortcut label="Clear Console" keys={['Ctrl', 'K']} />
                <Shortcut label="Toggle Settings" keys={['Ctrl', ',']} />
                <Shortcut label="Focus Input" keys={['/']} />
            </div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-glass-200 space-y-3">
         <button
           onClick={onReset}
           className="w-full bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 py-2.5 rounded-xl transition-all border border-red-500/20 hover:border-red-500/50 text-sm font-bold tracking-wide uppercase cursor-pointer"
         >
            Reset Session
         </button>
         <div className="text-center text-[10px] text-gray-600 font-mono">
           Hybrid Conductor v{version}
         </div>
      </div>
    </div>
  );
};

const Slider = ({ label, value, color, onChange, hint }) => (
    <div className="space-y-2 group">
        <div className="flex justify-between text-xs font-medium">
            <div>
              <span className="group-hover:text-white transition-colors">{label}</span>
              {hint && <p className="text-[10px] text-gray-600 mt-0.5">{hint}</p>}
            </div>
            <span className={`text-${color}-400 font-mono`}>{value}%</span>
        </div>
        <div className="relative h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
             <div
                className={`absolute top-0 left-0 h-full rounded-full bg-gradient-to-r from-${color === 'accent' ? 'pink-500' : 'indigo-500'} to-${color === 'accent' ? 'purple-500' : 'blue-500'}`}
                style={{ width: `${value}%` }}
             />
             <input
                type="range"
                className="absolute inset-0 opacity-0 cursor-pointer"
                min="0"
                max="100"
                value={value}
                onChange={(e) => onChange(e.target.value)}
             />
        </div>
    </div>
);

const Toggle = ({ label, checked, onChange, hint }) => (
  <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5 hover:border-white/10 transition-colors">
    <div>
      <span className="text-xs text-gray-300 font-medium">{label}</span>
      {hint && <p className="text-[10px] text-gray-600 mt-0.5">{hint}</p>}
    </div>
    <button
      onClick={() => onChange(!checked)}
      className={`relative w-10 h-5 rounded-full transition-colors cursor-pointer ${checked ? 'bg-primary' : 'bg-gray-700'}`}
    >
      <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${checked ? 'translate-x-5' : 'translate-x-0.5'}`} />
    </button>
  </div>
);

const Shortcut = ({ label, keys }) => (
    <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/5 hover:border-white/10 transition-colors">
        <span className="text-xs text-gray-400 font-medium">{label}</span>
        <div className="flex gap-1">
            {keys.map(k => (
                <kbd key={k} className="min-w-[20px] px-1.5 py-0.5 bg-gray-900 rounded border-b-2 border-gray-700 font-mono text-[10px] text-gray-300 shadow-sm text-center">{k}</kbd>
            ))}
        </div>
    </div>
);

export default Settings;
