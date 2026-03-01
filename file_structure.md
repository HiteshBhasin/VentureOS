aef-platform/
│
├── apps/                     # Deployable services
│   ├── api/                  # Main backend API (Node.js)
│   ├── agent-engine/         # Agent runtime service
│   ├── orchestrator/         # Task + spawning logic
│   ├── dashboard/            # Next.js frontend
│   └── compliance/           # Audit & logging service
│
├── packages/                 # Shared internal libraries
│   ├── core/                 # Shared types, configs, constants
│   ├── agent-sdk/            # Base Agent class + utilities
│   ├── memory/               # Knowledge Lake interface
│   ├── events/               # Event bus logic (Redis)
│   └── utils/                # Shared helpers
│
├── infrastructure/           # DevOps layer
│   ├── docker/
│   ├── kubernetes/
│   ├── terraform/
│   └── nginx/
│
├── docs/
├── scripts/
├── .env
├── docker-compose.yml
└── README.md