'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useLearningSession } from '@/contexts/LearningSessionContext';
import { useRouter } from 'next/navigation';

export default function SidePanel() {
  const router = useRouter();
  const { user, signOut } = useAuth();
  const { currentSession, stats } = useLearningSession();

  return (
    <div className="w-64 min-h-screen bg-gray-800 text-white p-4 flex flex-col overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-lg font-bold mb-2">Profile</h2>
        {user && (
          <div className="text-sm">
            <p className="mb-1 font-medium truncate">{user.username || 'Student'}</p>
            <p className="mb-2 text-gray-400 text-xs truncate">{user.email}</p>
            <button
              onClick={async () => {
                await signOut();
                router.refresh();
              }}
              className="w-full px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Sign Out
            </button>
          </div>
        )}
      </div>

      {currentSession && (
        <div className="mb-6">
          <h2 className="text-lg font-bold mb-2">Current Session</h2>
          <div className="bg-gray-700 rounded-lg p-3 space-y-1.5">
            <div>
              <span className="text-gray-400">Score:</span>{' '}
              <span className="font-medium">{currentSession.score}</span>
            </div>
            <div>
              <span className="text-gray-400">Problems:</span>{' '}
              <span className="font-medium">
                {currentSession.problems_solved}/{currentSession.problems_attempted}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Hints:</span>{' '}
              <span className="font-medium">{currentSession.hints_used}</span>
            </div>
          </div>
        </div>
      )}

      {stats && (
        <div>
          <h2 className="text-lg font-bold mb-2">Overall Progress</h2>
          <div className="bg-gray-700 rounded-lg p-3 space-y-1.5">
            <div>
              <span className="text-gray-400">Total:</span>{' '}
              <span className="font-medium">{stats.totalProblemsAttempted}</span>
            </div>
            <div>
              <span className="text-gray-400">Solved:</span>{' '}
              <span className="font-medium">{stats.totalProblemsSolved}</span>
            </div>
            <div>
              <span className="text-gray-400">Accuracy:</span>{' '}
              <span className="font-medium">{stats.accuracy.toFixed(1)}%</span>
            </div>
            <div>
              <span className="text-gray-400">Avg. Hints:</span>{' '}
              <span className="font-medium">{stats.averageHintsUsed.toFixed(1)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
