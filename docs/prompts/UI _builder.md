## Refined UI/UX Prompt for Ralph Orchestrator Dashboard

```
**PROMPT: Create Production-Ready Ralph Orchestrator Dashboard v8.0**

**CONTEXT:** Transform the existing `dashboard/app.py` into a **highly interactive, responsive, visually stunning** web interface that rivals OpenHands.dev while incorporating Ralph's unique iteration-based workflow. Target audience: Developers who demand instant feedback, detailed progress tracking, and keyboard-driven efficiency.

**ROLE:** You are a senior frontend architect + UX designer specializing in AI developer tools. Deliver production-ready React + Tailwind CSS + Flask SSE implementation.

**SPECIFICATION:**

### 🎨 **DESIGN SYSTEM** (Dribbble-Inspired)
```
Primary: #1e3a8a (Deep Indigo)     Accent: #3b82f6 (Bright Blue)  
Secondary: #0f172a (Slate 900)     Success: #10b981 (Emerald)  
Warning: #f59e0b (Amber)           Danger: #ef4444 (Red 500)
Glassmorphism: backdrop-blur-md, bg-white/10, border-white/20
Gradients: from-indigo-500 to-blue-600, from-emerald-500 to-teal-600
```

### 📱 **RESPONSIVE LAYOUT** (Mobile-First)
```
Desktop (1440px+): 5-column grid | Sidebar | Main | Console | Progress | Settings
Tablet (768px): 3-column | Collapsible sidebar | Stacked main/console
Mobile (375px): Fullscreen entry | Collapsible panels | Touch-optimized
```

### 🖥️ **CORE COMPONENTS** (All Must Exist)

#### 1. **Resizable Entry Field** (60% Priority)
```
- Min 100px / Max 60% viewport height
- Auto-expanding textarea (like VS Code terminal input)
- Glassmorphism design (Dribbble shot reference)
- Features:
  * Keyboard shortcuts: Ctrl+Enter (send), Ctrl+↑↓ (history)  
  * Typing indicators ("Ralph is thinking...")
  * Placeholder: "Describe your task... (e.g., 'Create user auth system')"
  * Character counter + estimated token cost
  * Drag-to-resize handle (bottom-right corner)
```

#### 2. **High-Level Steps & Iterations View** (Priority 1)
```
Real-time SSE-fed progress tree:
```
```
Ralph v8.0 [🟢 Live]                    [⚙️ Settings] [📊 Stats]
┌─ 1. Planning (3/3) ✓  [00:12]         Console ▼
│  ├─ Analyze requirements ✓            [Entry Field - Drag to resize ↓]
│  ├─ Generate plan ✓                   "Build user dashboard..."
│  └─ Create file structure ✓           [Send] [History ▼] (247 chars)
└─ 2. Implementation (1/5) ⏳ [00:45]   
   ├─ loop_guardian.py [100%] ✓         
   ├─ cartographer.py [75%] ⏳         
   ├─ context_fetcher.py [0%] ⏳  
   ├─ worker.py [0%] ─
   └─ dashboard/app.py [0%] ─
```
```
- Clickable steps expand to show file diffs, logs, errors
- Progress bars with eta predictions
- Color-coded status: ✓ Green | ⏳ Yellow | ❌ Red | 🔄 Blue (retrying)
- Collapsible iteration history (v7.2 → v8.0)
```

#### 3. **Console View** (Developer Essential)
```
Split-pane resizable console (30% bottom viewport):
- Tabbed interface: Logs | Errors | Debug | Network
- Auto-scroll with pause/resume toggle  
- Filter: All | Errors | Warnings | Info | Verbose
- Copy-to-clipboard per line
- Live search (Ctrl+F)
- Dark theme optimized for long debugging sessions
```

#### 4. **Settings Panel** (Advanced Controls)
```
⊞ Collapsible sidebar (24px trigger) containing:
```
```
COMPLEXITY       LLM MODEL        TEMPERATURE
[Fast ●] [Med]   [Gemini 3.0 ●]   [0.7 ●] [1.0] [1.3]
[Deep ] [Max ]   [Claude 3.5]     Retry: [1●] [codelabs.developers.google](https://codelabs.developers.google.com/getting-started-google-antigravity)

CONTEXT WINDOW   TOOL INTEGRATIONS
[Full ●] [Slim]  [Openground ✓] [MCP Git ✓] [Codesum ✓]
[Med  ] [Mini]   [ ] [ ] [ ]     

SHORTCUTS        PERFORMANCE
[VSCode ●]       [Turbo ●] [Balanced] [Precise]
[OpenHands]      Memory: 4.2GB/8GB
[Ralph ]         GPU: [NVIDIA ✓]
```

#### 5. **Keyboard-Driven Shortcuts** (Power User Required)
```
Global Shortcuts (Non-conflicting):
Ctrl+Enter     → Send prompt  
Ctrl+Shift+E   → Toggle console  
Ctrl+Shift+P   → Toggle settings  
Ctrl+↑/↓       → Prompt history  
Ctrl+K         → Clear console  
Esc            → Focus entry field  
Tab            → Next panel / Cycle focus  
```

### 🔧 **Backend Updates Required** (Flask + SSE)

#### **New SSE Endpoints:**
```python
@app.route('/api/stream')  # Main progress stream  
@app.route('/api/console') # Real-time console logs
@app.route('/api/stats')   # System stats + memory usage
@app.route('/api/history') # Prompt/response history
```

#### **Payload Structure:**
```json
{
  "timestamp": "2026-02-13T19:13:00Z",
  "type": "progress|console|error|stats",
  "data": {
    "step": "Implementation",
    "file": "loop_guardian.py", 
    "progress": 87,
    "eta": "2m 15s",
    "logs": ["Hash normalization complete", "Test 4/5 passed"]
  }
}
```

### 📊 **Real-Time Metrics Dashboard**
```
Top-right corner always visible:
CPU: 23% | MEM: 4.2/8GB | GPU: 67% | Iterations: 47 
Uptime: 2h 13m | Cost: $0.47 | Success: 94%
[🔄 Refresh] [⚠️ 2 Warnings]
```

### 🎯 **SUCCESS CRITERIA**
```
✅ Responsive across all devices (375px → 4K)
✅ Glassmorphism + gradient design (Dribbble quality)  
✅ Resizable entry field + console (split-pane)
✅ Real-time step/iteration progress tree
✅ Keyboard shortcuts work instantly
✅ SSE streams update UI without refresh
✅ Settings persist to localStorage
✅ Console searchable + copyable + filterable
✅ Dark/Light theme toggle
✅ 60fps smooth animations (no jank)
✅ Load time < 2 seconds
✅ Zero-configuration deployment
```

**DELIVERABLE FORMAT:**
```
1. Complete React + Tailwind implementation (App.jsx, components/)
2. Updated Flask backend (dashboard/app.py) with SSE endpoints
3. CSS design system (tailwind.config.js + globals.css)
4. Sample data generator for development
5. Keyboard shortcut cheat sheet
6. Mobile-responsive screenshots
```

**REFERENCES:**
- Ralph Orchestrator: https://github.com/mikeyobrien/ralph-orchestrator (workflow)
- OpenHands: https://openhands.dev/ (styling inspiration)  
- Dribbble: https://dribbble.com/shots/23079555 (glassmorphism input field)

**CONSTRAINTS:**
- No external paid services
- Works offline after initial load
- PWA-capable (installable)
- Lighthouse score > 95/100
- Bundle size < 500KB gzipped

---
**OUTPUT:** Complete production-ready codebase ready for `npm run dev` deployment.
```

***

## **Key Improvements Made:**

1. **✅ Specificity**: Exact hex colors, breakpoints, component layouts
2. **✅ Developer-Focused**: Keyboard shortcuts, console debugging, real-time metrics  
3. **✅ Production-Ready**: SSE payloads, backend endpoints, performance targets
4. **✅ Visual Excellence**: Glassmorphism + gradients + responsive design system
5. **✅ Measurable Success**: Lighthouse scores, bundle size, load times
6. **✅ Ralph-Specific**: Iteration trees, complexity sliders, Openground integration

**Ready to copy-paste into your AI?** This will generate a dashboard that developers will actually love using.
