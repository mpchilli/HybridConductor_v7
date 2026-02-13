import { useEffect } from 'react';

export const useKeyboard = (shortcuts) => {
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Build the key combination string
      const parts = [];
      if (e.ctrlKey || e.metaKey) parts.push('Ctrl');
      if (e.altKey) parts.push('Alt');
      if (e.shiftKey) parts.push('Shift');
      
      // Handle special keys or regular keys
      let key = e.key;
      if (key === ' ') key = 'Space';
      if (key === ',') key = ','; // Explicitly handle comma
      
      // If it's a character key, uppercase it for consistency with "Ctrl+K"
      if (key.length === 1) key = key.toUpperCase();
      
      parts.push(key);
      const combo = parts.join('+');

      // Check for match
      // Try combo first, then just the key
      const handler = shortcuts[combo] || shortcuts[e.key];
      
      if (handler) {
        e.preventDefault();
        handler(e);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
};
