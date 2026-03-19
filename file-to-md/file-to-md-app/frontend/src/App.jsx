import { useState } from 'react';
import { FileText, Globe, AlertCircle } from 'lucide-react';
import FileUploader from './components/FileUploader';
import UrlInput from './components/UrlInput';
import MarkdownPreview from './components/MarkdownPreview';

export default function App() {
  const [activeTab, setActiveTab] = useState('file');
  const [markdown, setMarkdown] = useState('');
  const [error, setError] = useState('');

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-4 md:p-8">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <header className="text-center">
          <h1 className="text-3xl md:text-4xl font-bold text-indigo-900 mb-2">
            File to Markdown
          </h1>
          <p className="text-gray-500">
            Convierte archivos y URLs a Markdown en segundos
          </p>
        </header>

        {/* Tabs */}
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setActiveTab('file')}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-colors ${
              activeTab === 'file'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200'
                : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            <FileText size={20} />
            Archivo
          </button>
          <button
            onClick={() => setActiveTab('url')}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-colors ${
              activeTab === 'url'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200'
                : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            <Globe size={20} />
            URL
          </button>
        </div>

        {/* Input area */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          {activeTab === 'file' ? (
            <FileUploader onResult={setMarkdown} onError={setError} />
          ) : (
            <UrlInput onResult={setMarkdown} onError={setError} />
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
            <AlertCircle size={20} />
            <p>{error}</p>
          </div>
        )}

        {/* Result */}
        {markdown && (
          <MarkdownPreview markdown={markdown} onChange={setMarkdown} />
        )}

        {/* Footer */}
        <footer className="text-center text-sm text-gray-400 pt-4">
          File to Markdown v1.0
        </footer>
      </div>
    </div>
  );
}
