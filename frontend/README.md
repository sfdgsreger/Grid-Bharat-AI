# Bharat-Grid AI Frontend

Real-time energy distribution optimization dashboard built with React 18, TypeScript, and Tailwind CSS.

## Features

- **React 18** with TypeScript for type safety
- **Tailwind CSS** for responsive styling
- **React Router** for navigation (ready for future expansion)
- **Vite** for fast development and building
- **Vitest** for testing
- **ESLint** for code quality

## Project Structure

```
src/
├── components/          # React components
│   └── Layout.tsx      # Main layout component
├── hooks/              # Custom React hooks (ready for WebSocket hook)
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
├── constants/          # Configuration constants
├── test/               # Test files
├── App.tsx             # Main application component
├── main.tsx            # Application entry point
├── router.tsx          # Router configuration
└── index.css           # Global styles with Tailwind
```

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Run tests:
   ```bash
   npm test
   ```

4. Build for production:
   ```bash
   npm run build
   ```

## Configuration

- **API Base URL**: Configure via `VITE_API_BASE_URL` environment variable
- **WebSocket URL**: Configure via `VITE_WS_BASE_URL` environment variable
- **Proxy**: Vite is configured to proxy `/api` and `/ws` requests to the backend

## Upcoming Components

The dashboard foundation is ready for the following components to be implemented:

- **Power Connection Map** (Task 9.1) - Interactive visualization of energy nodes
- **Real-time Gauges** (Task 9.2) - Supply and demand metrics
- **Live Stream Table** (Task 9.3) - Recent allocation results
- **Simulation Control Panel** (Task 9.4) - Grid failure simulation interface
- **WebSocket Client Hook** (Task 8.2) - Real-time data connection

## Performance Targets

- **Dashboard FPS**: 60fps during updates
- **WebSocket Latency**: <50ms for real-time updates
- **Responsive Design**: Mobile-first approach with Tailwind CSS

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Vite** - Build tool and dev server
- **Vitest** - Testing framework
- **Lucide React** - Icon library