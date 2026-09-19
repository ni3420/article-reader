'use client';

import React, { useState } from 'react';
import Url from '@/components/url_upload'; 
import Chat from '@/components/chat'; 

export default function Home() {
  const [activeTab, setActiveTab] = useState<'url' | 'chat'>('url');
  const [isUploading, setIsUploading] = useState(false);

  return (
    <main className="min-h-screen bg-gray-100 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Article Reader RAG</h1>
          <p className="text-sm text-gray-500 mt-1">Upload articles and chat with them using local AI</p>
        </div>

        <div className="flex justify-center gap-4 mb-6">
          <button
            onClick={() => setActiveTab('url')}
            disabled={isUploading}
            className={`px-6 py-2.5 rounded-xl font-medium text-sm transition-all cursor-pointer ${
              activeTab === 'url'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-200'
                : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
            } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            Upload URL
          </button>
          
          <button
            onClick={() => setActiveTab('chat')}
            disabled={isUploading}
            className={`px-6 py-2.5 rounded-xl font-medium text-sm transition-all cursor-pointer ${
              activeTab === 'chat'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-200'
                : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
            } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            Chat with LLM
          </button>
        </div>

        <div className="transition-all duration-300">
          {activeTab === 'url' ? (
            <Url setIsUploading={setIsUploading} />
          ) : (
            <Chat />
          )}
        </div>
      </div>
    </main>
  );
}