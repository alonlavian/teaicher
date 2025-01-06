'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from './AuthContext';
import { supabase } from '@/utils/supabase';
import { Database } from '@/types/database';

type LearningSession = Database['public']['Tables']['learning_sessions']['Row'];

interface LearningSessionContextType {
  currentSession: LearningSession | null;
  loading: boolean;
  startNewSession: () => Promise<void>;
  updateSession: (updates: Partial<LearningSession>) => Promise<void>;
  stats: {
    totalProblemsAttempted: number;
    totalProblemsSolved: number;
    accuracy: number;
    averageHintsUsed: number;
  };
}

const defaultStats = {
  totalProblemsAttempted: 0,
  totalProblemsSolved: 0,
  accuracy: 0,
  averageHintsUsed: 0,
};

const LearningSessionContext = createContext<LearningSessionContextType>({
  currentSession: null,
  loading: true,
  startNewSession: async () => {},
  updateSession: async () => {},
  stats: defaultStats,
});

export const useLearningSession = () => {
  const context = useContext(LearningSessionContext);
  if (context === undefined) {
    throw new Error('useLearningSession must be used within a LearningSessionProvider');
  }
  return context;
};

export function LearningSessionProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [currentSession, setCurrentSession] = useState<LearningSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(defaultStats);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    const initializeSession = async () => {
      if (!user || initialized) return;
      
      setLoading(true);
      try {
        await Promise.all([loadCurrentSession(), loadStats()]);
      } catch (error) {
        console.error('Error initializing session:', error);
      } finally {
        setLoading(false);
        setInitialized(true);
      }
    };

    initializeSession();
  }, [user, initialized]);

  const loadCurrentSession = async () => {
    if (!user) return;

    try {
      const { data: session, error } = await supabase
        .from('learning_sessions')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
        .limit(1)
        .single();

      if (error) throw error;
      setCurrentSession(session);
    } catch (error) {
      console.error('Error loading session:', error);
    }
  };

  const loadStats = async () => {
    if (!user) return;

    try {
      const { data, error } = await supabase
        .from('learning_sessions')
        .select('*')
        .eq('user_id', user.id);

      if (error) throw error;

      if (data && data.length > 0) {
        const totalAttempted = data.reduce((sum, session) => sum + session.problems_attempted, 0);
        const totalSolved = data.reduce((sum, session) => sum + session.problems_solved, 0);
        const totalHints = data.reduce((sum, session) => sum + session.hints_used, 0);

        setStats({
          totalProblemsAttempted: totalAttempted,
          totalProblemsSolved: totalSolved,
          accuracy: totalAttempted > 0 ? (totalSolved / totalAttempted) * 100 : 0,
          averageHintsUsed: totalAttempted > 0 ? totalHints / totalAttempted : 0,
        });
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const startNewSession = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const { data: session, error } = await supabase
        .from('learning_sessions')
        .insert({
          subject: 'math',
          started_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
        })
        .select()
        .single();

      if (error) throw error;
      setCurrentSession(session);
      await loadStats();
    } catch (error) {
      console.error('Error starting new session:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateSession = async (updates: Partial<LearningSession>) => {
    if (!currentSession || !user) return;

    try {
      const { data: session, error } = await supabase
        .from('learning_sessions')
        .update(updates)
        .eq('id', currentSession.id)
        .select()
        .single();

      if (error) throw error;
      setCurrentSession(session);
      await loadStats();
    } catch (error) {
      console.error('Error updating session:', error);
    }
  };

  return (
    <LearningSessionContext.Provider
      value={{
        currentSession,
        loading,
        startNewSession,
        updateSession,
        stats,
      }}
    >
      {children}
    </LearningSessionContext.Provider>
  );
}
