import { Message } from '@/types/chat';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage = ({ message }: ChatMessageProps) => {
  const isTeacher = message.role === 'assistant';

  return (
    <div className={`flex ${isTeacher ? 'justify-start' : 'justify-end'} mb-4`}>
      <div
        className={`max-w-[80%] p-3 rounded-lg ${
          isTeacher
            ? 'bg-blue-100 text-blue-900'
            : 'bg-green-100 text-green-900'
        }`}
      >
        <div className="text-sm font-semibold mb-1">
          {isTeacher ? 'Teacher' : 'You'}
        </div>
        <div className="whitespace-pre-wrap">{message.content}</div>
      </div>
    </div>
  );
};

export default ChatMessage;
