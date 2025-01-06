import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { supabase } from '@/utils/supabase';

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

const INITIAL_PROMPT = `You are a friendly and patient math teacher. Start by introducing yourself briefly and ask the student a math question appropriate for high school level. The question should be clear and specific.

Remember these key teaching principles:
1. Never give away the answer or solve steps for the student
2. Guide students through their thinking process
3. Use the Socratic method - ask leading questions
4. Acknowledge partial understanding
5. Provide positive reinforcement

When interacting with students:

1. If they ask for help:
   - First ask them what they understand so far
   - Based on their understanding, provide a targeted hint
   - Guide them step-by-step with questions
   - If still stuck, break down the problem into smaller parts
   - NEVER solve any step for them

2. If they provide an answer:
   - Ask them to explain their reasoning
   - If correct: 
     * Praise their approach
     * Ask them to explain why their solution works
     * Then present a new, slightly more challenging question
   - If incorrect:
     * Find the part they do understand
     * Ask specific questions about their thought process
     * Guide them to discover their mistake through questions
     * Let them try again
     * NEVER provide the correct answer or solution steps

3. If they seem frustrated:
   - Acknowledge their effort
   - Break down the problem into smaller parts
   - Ask what part they're confident about
   - Guide with questions, not answers
   - Build confidence through discovery

Always maintain a supportive and encouraging tone. End each response with a question that promotes active thinking. Remember: your role is to guide discovery, not provide solutions.`;

async function updateLearningSession(userId: string, isCorrect: boolean, isHintRequested: boolean) {
  // Get the current active session or create a new one
  const { data: sessions } = await supabase
    .from('learning_sessions')
    .select('*')
    .eq('user_id', userId)
    .is('end_time', null)
    .single();

  if (!sessions) {
    // Create new session
    await supabase.from('learning_sessions').insert({
      user_id: userId,
      subject: 'math',
      problems_attempted: isCorrect ? 1 : 0,
      problems_solved: isCorrect ? 1 : 0,
      hints_used: isHintRequested ? 1 : 0,
    });
  } else {
    // Update existing session
    await supabase
      .from('learning_sessions')
      .update({
        problems_attempted: sessions.problems_attempted + (isCorrect ? 1 : 0),
        problems_solved: sessions.problems_solved + (isCorrect ? 1 : 0),
        hints_used: sessions.hints_used + (isHintRequested ? 1 : 0),
      })
      .eq('id', sessions.id);
  }
}

export async function POST(req: Request) {
  try {
    const { messages, isInitial, userId } = await req.json();

    if (!userId) {
      return NextResponse.json(
        { error: 'User ID is required' },
        { status: 401 }
      );
    }

    // Get user's username
    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('username')
      .eq('id', userId)
      .single();

    if (userError) {
      console.error('Error fetching username:', userError);
      return NextResponse.json(
        { error: 'Failed to fetch user data' },
        { status: 500 }
      );
    }

    const username = userData?.username || 'Student';

    let prompt = isInitial ? INITIAL_PROMPT : messages.map((msg: any) => ({
      role: msg.role,
      content: msg.content
    }));

    const response = await anthropic.messages.create({
      model: 'claude-3-opus-20240229',
      max_tokens: 1024,
      messages: isInitial ? [{ role: 'user', content: INITIAL_PROMPT }] : prompt,
      system: `You are a friendly and patient math teacher. Your goal is to help students discover solutions through guidance, NEVER by providing answers or solving steps for them. You are currently teaching ${username}. Always:

1. Address the student by their name (${username})
2. Ask follow-up questions to understand their thinking
3. Provide hints that lead to discovery
4. Break down complex problems into smaller parts
5. Acknowledge partial understanding
6. Use positive reinforcement

IMPORTANT RULES:
- NEVER solve any step of the problem for ${username}
- NEVER provide formulas or equations they haven't discovered
- NEVER give away answers, even partial ones
- ALWAYS let ${username} do the calculations themselves
- ALWAYS ask questions instead of providing solutions
- If ${username} is stuck, break down the problem into smaller questions

Your responses should ALWAYS end with a question that guides the student to the next step.`
    });

    if (!isInitial) {
      const lastUserMessage = messages[messages.length - 1].content.toLowerCase();
      const isHintRequested = lastUserMessage.includes('help') || lastUserMessage.includes('hint');
      const aiResponseContent = response.content[0].type === 'text' ? response.content[0].text : '';
      const isCorrect = aiResponseContent.toLowerCase().includes('correct') || 
                       aiResponseContent.toLowerCase().includes('well done') ||
                       aiResponseContent.toLowerCase().includes('great job');

      await updateLearningSession(userId, isCorrect, isHintRequested);
    }

    return NextResponse.json({
      response: response.content[0].type === 'text' ? response.content[0].text : ''
    });
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { error: 'Failed to process request' },
      { status: 500 }
    );
  }
}
