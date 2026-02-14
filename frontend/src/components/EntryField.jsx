import React, { useState, useRef, useEffect } from 'react';

const EntryField = ({ onSend, disabled = false }) => {
  const [input, setInput] = useState('');
  const [height, setHeight] = useState(100);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);
  const textareaRef = useRef(null);

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSend();
    }
  };

  const handleSend = () => {
    if (!input.trim() || disabled) return;
    if (onSend) onSend(input);
    setInput('');
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging) return;
      if (containerRef.current) {
         const newHeight = e.clientY - containerRef.current.getBoundingClientRect().top;
         if (newHeight > 60 && newHeight < 500) {
            setHeight(newHeight);
         }
      }
    };
    const handleMouseUp = () => setIsDragging(false);

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  return (
    <div
        ref={containerRef}
        className={`relative bg-glass-100 backdrop-blur-md rounded-2xl border border-glass-200 p-4 transition-all focus-within:ring-2 ring-primary/50 flex flex-col group ${disabled ? 'opacity-60' : ''}`}
        style={{ height: `${height}px` }}
    >
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className="flex-1 w-full bg-transparent border-none outline-none text-white placeholder-gray-400 resize-none font-mono text-sm leading-relaxed disabled:cursor-not-allowed"
        placeholder={disabled ? "Orchestrator is running... wait for completion or reset." : "Describe your task... (Ctrl+Enter to run)"}
      />

      <div className="flex justify-between items-center mt-2 opacity-50 group-hover:opacity-100 transition-opacity">
         <div
            className="cursor-ns-resize p-1.5 hover:bg-glass-200 rounded transition-colors text-gray-500 hover:text-white"
            onMouseDown={() => setIsDragging(true)}
            title="Drag to resize"
         >
            {/* Grip Dots */}
            <svg width="24" height="4" viewBox="0 0 24 4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <circle cx="2" cy="2" r="1" fill="currentColor" stroke="none"/>
                <circle cx="12" cy="2" r="1" fill="currentColor" stroke="none"/>
                <circle cx="22" cy="2" r="1" fill="currentColor" stroke="none"/>
            </svg>
         </div>

         <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500 font-mono">{input.length} chars</span>
            <button
              onClick={handleSend}
              disabled={disabled || !input.trim()}
              className="bg-primary/80 hover:bg-primary text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-all shadow-lg hover:shadow-primary/20 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              {disabled ? 'Busy' : 'Run'}
            </button>
         </div>
      </div>
    </div>
  );
};

export default EntryField;
