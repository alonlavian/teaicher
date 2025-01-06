export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: number
          username: string
          email: string
          created_at: string
          preferred_language: string
          total_score: number
        }
        Insert: {
          username: string
          email: string
          preferred_language?: string
          total_score?: number
        }
        Update: {
          username?: string
          email?: string
          preferred_language?: string
          total_score?: number
        }
      }
      learning_sessions: {
        Row: {
          id: string;
          user_id: string;
          subject: string;
          started_at: string;
          problems_attempted: number;
          problems_solved: number;
          hints_used: number;
          score: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id?: string;
          subject: string;
          started_at?: string;
          problems_attempted?: number;
          problems_solved?: number;
          hints_used?: number;
          score?: number;
          created_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          subject?: string;
          started_at?: string;
          problems_attempted?: number;
          problems_solved?: number;
          hints_used?: number;
          score?: number;
          created_at?: string;
        };
      };
    };
  };
}
