⚡ Blitz Arena

Blitz Arena is a fast-paced, real-time multiplayer quiz and trivia platform designed for live classrooms, competitive 1v1 battles, and high-energy group sessions. Inspired by platforms like Buzrr, Blooket, and Kahoot, Blitz Arena combines instant room-code matchmaking with gamified power-ups and live leaderboards.

✨ Features

⚡ Real-Time Multiplayer Rooms: Instant lobby creation with 6-digit PIN codes and zero-friction guest join.

🎮 Multiple Game Modes:

Classic Blitz: Speed-based scoring where faster accurate answers earn bonus streak multipliers.

1v1 Ranked Arena: Head-to-head matchmaking with live ELO rating updates.

Power-Up Mayhem: Earn points to trigger shields, score multipliers, or freeze opponents' screens.

🤖 AI & Custom Quiz Builder: Create custom question decks manually or generate quizzes automatically from text/notes.

📊 Live Analytics & Podiums: Real-time answer distribution charts, post-game accuracy breakdowns, and animated winner podiums.

📱 Responsive Cross-Platform UI: Optimized for host projectors/desktops and player mobile devices.

🛠️ Tech Stack

(Update this section with your exact stack)

Frontend: React / Next.js, Tailwind CSS, Zustand / Redux

Backend: Node.js / NestJS / Django (or your chosen backend)

Real-Time Engine: WebSockets (Socket.io / Django Channels)

In-Memory State & Caching: Redis (for active game rooms, timers, and live leaderboards)

Database: PostgreSQL / MongoDB

Authentication: JWT / OAuth2 (with Guest Mode support)

🏗️ System Architecture

┌──────────────┐      WebSockets / HTTP      ┌──────────────────┐
│  Host Client │ ◄─────────────────────────► │                  │
└──────────────┘                             │   API & Socket   │
                                             │      Server      │
┌──────────────┐      WebSockets / HTTP      │                  │
│Player Clients│ ◄─────────────────────────► └────────┬─────────┘
└──────────────┘                                      │
                                       ┌──────────────┴──────────────┐
                                       ▼                             ▼
                              ┌─────────────────┐           ┌─────────────────┐
                              │      Redis      │           │   PostgreSQL    │
                              │ (Live Game State│           │ (Users, Decks,  │
                              │  & Leaderboards)│           │  Match History) │
                              └─────────────────┘           └─────────────────┘


🚀 Getting Started

Prerequisites

Node.js (v18+ recommended)

Redis (running locally or via Docker)

PostgreSQL (or your configured database)

1. Clone the Repository

git clone https://github.com/your-username/blitz-arena.git
cd blitz-arena


2. Environment Setup

Create a .env file in the root (and/or server / client directories) based on .env.example:

# Server
PORT=5000
NODE_ENV=development

# Database & Cache
DATABASE_URL=postgresql://user:password@localhost:5432/blitz_arena
REDIS_URL=redis://localhost:6379

# Auth & AI (Optional)
JWT_SECRET=your_super_secret_key
GEMINI_API_KEY=your_ai_api_key


3. Install Dependencies & Run

# Install dependencies
npm install

# Run database migrations (if applicable)
npm run db:migrate

# Start the development server
npm run dev


(Alternatively, using Docker Compose:)

docker-compose up --build


📂 Project Structure

blitz-arena/
├── client/                 # Frontend application
│   ├── src/
│   │   ├── components/     # UI components (Lobby, Timer, Leaderboard, QuestionCard)
│   │   ├── hooks/          # Custom WebSocket & game state hooks
│   │   ├── pages/          # Host, Player, Dashboard, and Quiz Builder views
│   │   └── store/          # Client state management
├── server/                 # Backend API & WebSocket server
│   ├── src/
│   │   ├── sockets/        # Real-time room, buzzer, and scoring event handlers
│   │   ├── controllers/    # REST endpoints for quizzes, auth, and stats
│   │   ├── services/       # Game loop engine, ELO calculator, AI generator
│   │   └── models/         # Database schemas
├── docker-compose.yml      # Container orchestration for App, Redis, and DB
└── README.md
