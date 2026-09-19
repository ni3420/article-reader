import React, { useState } from 'react';

interface UrlProps {
  setIsUploading?: (loading: boolean) => void;
}

const Url: React.FC<UrlProps> = ({ setIsUploading }) => {
  const [url, setUrl] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');
  const [isError, setIsError] = useState<boolean>(false);

  const updateLoadingState = (status: boolean) => {
    setLoading(status);
    if (setIsUploading) {
      setIsUploading(status);
    }
  };

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    updateLoadingState(true);
    setMessage('');
    setIsError(false);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_SERVER_URL}/url?Url=${encodeURIComponent(url)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(data.msg || 'Article successfully processed and embedded!');
        setUrl('');
      } else {
        setIsError(true);
        setMessage(`Error: ${data.detail || 'Failed to upload article'}`);
      }
    } catch (error) {
      setIsError(true);
      setMessage(error instanceof Error ? `Error: ${error.message}` : 'An unexpected error occurred');
    } finally {
      updateLoadingState(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-12 p-6 bg-white border border-gray-200 rounded-xl shadow-md">
      <h2 className="text-xl font-bold text-gray-800 mb-4">Upload Article URL</h2>
      
      <form onSubmit={handleUpload} className="flex flex-col gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Article Link
          </label>
          <input
            type="url"
            placeholder="https://example.com/article"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            className="w-full px-4 py-2 text-sm text-gray-900 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm rounded-lg transition-colors cursor-pointer disabled:bg-blue-300 disabled:cursor-not-allowed"
        >
          {loading ? 'Processing & Embedding...' : 'Upload & Embed'}
        </button>
      </form>

      {message && (
        <p className={`mt-4 text-sm text-center p-3 rounded-lg ${isError ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-700'}`}>
          {message}
        </p>
      )}
    </div>
  );
};

export default Url;