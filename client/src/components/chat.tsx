'use client';

import React, { useState, FormEvent, useEffect, useRef } from 'react';

interface Message {
  sender: 'user' | 'ai';
  text: string;
}

const Chat: React.FC = () => {
  const [url, setUrl] = useState<string>('');
  const [question, setQuestion] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      import('eruda').then((eruda) => {
        eruda.default.init();
      });
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSendMessage = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!question.trim() || !url.trim()) {
      setError('Please provide both an Article URL and a question.');
      return;
    }

    setError('');
    const userMessage = question;
    setQuestion('');

    setMessages((prev) => [...prev, { sender: 'user', text: userMessage }]);
    setLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_SERVER_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          text: userMessage,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessages((prev) => [...prev, { sender: 'ai', text: data.answer }]);
      } else {
        setError(`Error: ${data.detail || 'Failed to fetch response'}`);
      }
    } catch (err) {
      setError('Error: Failed to connect to the backend server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto sm:mt-8 p-3 sm:p-6 bg-white sm:border sm:border-gray-100 sm:rounded-2xl sm:shadow-xl flex flex-col h-[100dvh] sm:h-[620px] w-full">
      <div className="flex items-center justify-between pb-3 mb-2 sm:mb-3 border-b border-gray-100 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
          <h2 className="text-base sm:text-lg font-semibold text-gray-900 tracking-tight">Article Assistant</h2>
        </div>
        <span className="text-xs font-medium text-gray-400 bg-gray-50 px-2.5 py-1 rounded-full border border-gray-100">
          AI Powered
        </span>
      </div>

      <div className="mb-2 sm:mb-3 shrink-0">
        <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
          Target Article Link
        </label>
        <input
          type="url"
          placeholder="https://example.com/article"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
          className="w-full px-3 py-2 text-sm text-gray-900 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none"
        />
      </div>

        <form onSubmit={handleSendMessage} className="flex gap-2 items-center shrink-0 pb-2 sm:pb-0">
        <input
          type="text"
          placeholder="Ask a question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={loading}
          className="flex-1 px-4 py-2.5 sm:py-3 text-sm text-gray-900 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 sm:px-5 py-2.5 sm:py-3 bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white font-medium text-sm rounded-xl transition-all shadow-sm shadow-indigo-500/20 cursor-pointer disabled:bg-indigo-300 disabled:cursor-not-allowed shrink-0 flex items-center justify-center"
        >
          Send
        </button>
      </form>

      <div className="flex-1 overflow-y-auto bg-slate-50/50 border border-gray-100 rounded-xl p-3 mb-2 sm:mb-3 flex flex-col gap-3 min-h-0">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-500 mb-2 font-bold text-sm">
              AI
            </div>
            <p className="text-sm font-medium text-gray-600">Drop a link and start asking questions</p>
            <p className="text-xs text-gray-400 mt-1">Get smart, contextual insights instantly.</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`max-w-[85%] sm:max-w-[80%] p-3 rounded-2xl text-sm leading-relaxed break-words shadow-sm ${
                msg.sender === 'user'
                  ? 'bg-indigo-600 text-white self-end rounded-br-xs'
                  : 'bg-white text-gray-800 border border-gray-100 self-start rounded-bl-xs'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>
            </div>
          ))
        )}
        {loading && (
          <div className="self-start bg-white text-gray-500 border border-gray-100 px-4 py-3 rounded-2xl text-sm animate-pulse shadow-xs flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" />
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce [animation-delay:0.2s]" />
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce [animation-delay:0.4s]" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="mb-2 px-3 py-2 bg-red-50 border border-red-100 rounded-xl shrink-0">
          <p className="text-xs text-red-600 font-medium">{error}</p>
        </div>
      )}

    
    </div>
  );
};

export default Chat;