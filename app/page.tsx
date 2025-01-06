'use client';

import { useState, useRef, useEffect } from 'react';
import { Message } from '@/types/chat';
import ChatMessage from '@/components/ChatMessage';
import { useAuth } from '@/contexts/AuthContext';
import { useLearningSession } from '@/contexts/LearningSessionContext';
import Auth from '@/components/Auth';
import SidePanel from '@/components/SidePanel';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  const { user, loading, signOut } = useAuth();
  const { 
    currentSession, 
    startNewSession, 
    updateSession, 
    stats,
    loading: sessionLoading 
  } = useLearningSession();
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasInitialized, setHasInitialized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    const initializeSession = async () => {
      if (!user || hasInitialized || sessionLoading) return;
      
      if (!currentSession) {
        await startNewSession();
      }
      
      if (messages.length === 0) {
        await handleInitialMessage();
      }
      
      setHasInitialized(true);
    };

    initializeSession();
  }, [user, sessionLoading, currentSession, hasInitialized]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleInitialMessage = async () => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: [],
        isInitial: true,
        userId: user?.id
      }),
    });
    
    const data = await response.json();
    setMessages([{
      role: 'assistant',
      content: data.response
    }]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !user || !currentSession) return;

    const userMessage: Message = {
      role: 'user',
      content: input
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          isInitial: false,
          userId: user.id
        }),
      });
      
      const data = await response.json();
      const aiMessage = {
        role: 'assistant',
        content: data.response
      };

      setMessages(prev => [...prev, aiMessage]);

      // Update session based on AI response
      const isHintRequested = userMessage.content.toLowerCase().includes('hint') || 
                             userMessage.content.toLowerCase().includes('help');
      const isCorrect = aiMessage.content.toLowerCase().includes('correct') || 
                       aiMessage.content.toLowerCase().includes('well done') ||
                       aiMessage.content.toLowerCase().includes('great job');

      await updateSession({
        problems_attempted: currentSession.problems_attempted + (isCorrect ? 1 : 0),
        problems_solved: currentSession.problems_solved + (isCorrect ? 1 : 0),
        hints_used: currentSession.hints_used + (isHintRequested ? 1 : 0),
        score: currentSession.score + (isCorrect ? 10 : 0)
      });

    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (loading || sessionLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center p-4">
        <div className="w-full max-w-md">
          <h1 className="text-2xl font-bold text-center mb-8">Welcome to Math Learning Assistant</h1>
          <Auth />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <SidePanel />
      <main className="flex-1 p-4 overflow-hidden">
        <div className="h-full max-w-3xl mx-auto bg-white rounded-lg shadow-lg overflow-hidden flex flex-col">
          <div className="p-3 bg-blue-600 text-white">
            <h1 className="text-lg font-bold">Math Learning Assistant</h1>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4">
            {messages.map((message, index) => (
              <ChatMessage key={index} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="p-3 border-t">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your answer or ask for help..."
                className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300"
              >
                {isLoading ? 'Thinking...' : 'Send'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
