orchestrator/dashboard/
├── app/
│ ├── layout.tsx # Root layout (wraps everything)
│ ├── page.tsx # Home page
│ ├── globals.css # Global styles
│ │
│ ├── (auth)/ # Auth routes group
│ │ ├── layout.tsx # Auth layout (separate from main)
│ │ ├── login/page.tsx
│ │ └── signup/page.tsx
│ │
│ ├── dashboard/ # Dashboard routes
│ │ ├── layout.tsx # Dashboard-specific layout (sidebar, nav)
│ │ ├── page.tsx # Main dashboard
│ │ ├── agents/page.tsx # Agents list
│ │ ├── tasks/page.tsx # Tasks list
│ │ └── [id]/page.tsx # Dynamic route (agent/task details)
│ │
│ ├── api/ # Backend API routes (run on server)
│ │ ├── agents/route.ts
│ │ ├── tasks/route.ts
│ │ └── auth/route.ts
│ │
│ └── error.tsx # Error boundary
│
├── components/ # Reusable components
│ ├── layout/
│ │ ├── Header.tsx
│ │ ├── Sidebar.tsx
│ │ ├── Navigation.tsx
│ │ └── Footer.tsx
│ │
│ ├── dashboard/
│ │ ├── AgentCard.tsx
│ │ ├── TaskList.tsx
│ │ └── StatusWidget.tsx
│ │
│ ├── common/
│ │ ├── Button.tsx
│ │ ├── Modal.tsx
│ │ ├── Loading.tsx
│ │ └── Error.tsx
│ │
│ └── forms/
│ ├── LoginForm.tsx
│ ├── CreateAgentForm.tsx
│ └── TaskForm.tsx
│
├── lib/ # Utility functions
│ ├── api.ts # API client (fetch requests)
│ ├── auth.ts # Auth utilities
│ ├── hooks.ts # Custom React hooks
│ └── utils.ts # Helper functions
│
├── hooks/ # Custom React hooks
│ ├── useAuth.ts
│ ├── useAgents.ts
│ └── useTasks.ts
│
├── contexts/ # React Context (state management)
│ ├── AuthContext.tsx
│ └── DashboardContext.tsx
│
├── types/ # TypeScript types
│ ├── agent.ts
│ ├── task.ts
│ └── api.ts
│
├── styles/ # Additional stylesheets
│ ├── dashboard.css
│ └── components.css
│
└── public/ # Static files
├── images/
├── icons/
└── next.svg

--How routes are working in Next.js 13 with the new app directory structure:
app/
├── page.tsx → localhost:3000/
├── dashboard/
│ └── page.tsx → localhost:3000/dashboard
├── dashboard/agents/
│ └── page.tsx → localhost:3000/dashboard/agents
├── dashboard/[id]/
│ └── page.tsx → localhost:3000/dashboard/123 (dynamic)
└── api/
└── agents/route.ts → localhost:3000/api/agents

-- Folder Grouping
app/
├── (auth)/
│ ├── layout.tsx # Only for auth pages
│ ├── login/page.tsx → /login
│ └── signup/page.tsx → /signup
│
└── (dashboard)/
├── layout.tsx # Only for dashboard pages
├── page.tsx → /
└── agents/page.tsx → /agents

Data Flow:
┌─────────────────────────────────────────┐
│ User Interface (React Components) │
│ - AgentCard.tsx, TaskList.tsx │
└────────────────┬────────────────────────┘
│
┌────────────────▼────────────────────────┐
│ Custom Hooks & Context │
│ - useAgents.ts, AuthContext.tsx │
└────────────────┬────────────────────────┘
│
┌────────────────▼────────────────────────┐
│ API Client (lib/api.ts) │
│ - Fetch requests to backend │
└────────────────┬────────────────────────┘
│
┌────────────────▼────────────────────────┐
│ Backend (Python Agent Engine) │
│ - venture-os/agent-engine/ │
└─────────────────────────────────────────┘
