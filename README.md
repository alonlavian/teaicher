# Teaicher

An intelligent learning assistant built with Next.js and TypeScript.

## Features

- Interactive chat-based learning interface
- User authentication and session management
- Real-time learning progress tracking
- Responsive design with Tailwind CSS

## Tech Stack

- Next.js 13+
- TypeScript
- Tailwind CSS
- React Context for state management

## Getting Started

### Prerequisites

- Node.js 16.8 or later
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
```

2. Install dependencies:
```bash
npm install
# or
yarn install
```

3. Create a `.env.local` file in the root directory with your environment variables:
```bash
# Add your environment variables here
```

4. Run the development server:
```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Project Structure

```
├── app/                # Next.js app directory
│   ├── api/           # API routes
│   ├── auth/          # Authentication pages
│   └── page.tsx       # Main application page
├── components/        # React components
├── contexts/         # React contexts
├── types/           # TypeScript type definitions
└── utils/           # Utility functions
```

## Development

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm start`: Start production server
- `npm run lint`: Run linting

## License

[Your chosen license]
