import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';
import { LearningSessionProvider } from '@/contexts/LearningSessionContext';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Math Learning Assistant',
  description: 'An AI-powered math learning assistant',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          {/* Remove LearningSessionProvider temporarily for testing */}
            {children}
        </AuthProvider>
      </body>
    </html>
  );
}
