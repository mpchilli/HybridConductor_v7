import React from 'react';

const Settings = ({ config, setConfig, onReset, onClose }) => {
  const updateConfig = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: parseInt(value) }));
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">Settings</h2>
        <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">✕</button>
      </div>

      <div className="space-y-8 flex-1 overflow-y-auto custom-scrollbar pr-2">
        {/* Complexity Section */}
        <div className="animate-in fade-in slide-in-from-right-4 duration-500">
            <h3 className="text-xs font-bold text-gray-500 mb-4 uppercase tracking-widest border-b border-gray-800 pb-1">Orchestrator Complexity</h3>
            <div className="space-y-6">
                <Slider 
                    label="Creativity" 
                    value={config.creativity} 
                    onChange={(v) => updateConfig('creativity', v)}
                    color="accent" 
                />
                <Slider 
                    label="Detail Level" 
                    value={config.detail} 
                    onChange={(v) => updateConfig('detail', v)}
                    color="primary" 
                />
                <Slider 
                    label="Context Window" 
                    value={config.context} 
                    onChange={(v) => updateConfig('context', v)}
                    color="blue" 
                />
            </div>
        </div>

        {/* Shortcuts Section */}
        <div className="animate-in fade-in slide-in-from-right-4 duration-700 delay-100">
            <h3 className="text-xs font-bold text-gray-500 mb-4 uppercase tracking-widest border-b border-gray-800 pb-1">Keyboard Shortcuts</h3>
            <div className="space-y-2 text-sm text-gray-300">
                <Shortcut label="Run Task" keys={['Ctrl', 'Enter']} />
                <Shortcut label="Clear Console" keys={['Ctrl', 'K']} />
                <Shortcut label="Toggle Settings" keys={['Ctrl', ',']} />
                <Shortcut label="Focus Input" keys={['/']} />
            </div>
        </div>
      </div>
      
      <div className="mt-4 pt-6 border-t border-glass-200">
         <button 
           onClick={onReset}
           className="w-full bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 py-3 rounded-xl transition-all border border-red-500/20 hover:border-red-500/50 text-sm font-bold tracking-wide uppercase"
         >
            Reset Session
         </button>
      </div>
    </div>
  );
};

const Slider = ({ label, value, color, onChange }) => (
    <div className="space-y-2 group">
        <div className="flex justify-between text-xs font-medium">
            <span className="group-hover:text-white transition-colors">{label}</span>
            <span className={`text-${color}-400`}>{value}%</span>
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
