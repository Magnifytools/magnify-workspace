import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Download, Check, Eye, Code } from 'lucide-react';

export default function MarkdownPreview({ markdown, onChange }) {
  const [copied, setCopied] = useState(false);
  const [view, setView] = useState('split'); // 'raw' | 'preview' | 'split'
  const [filename, setFilename] = useState('converted');

  const handleCopy = async () => {
    await navigator.clipboard.writeText(markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename || 'converted'}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
        <div className="flex gap-1">
          <button
            onClick={() => setView('raw')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              view === 'raw' ? 'bg-white shadow-sm text-indigo-700' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Code size={14} />
            Raw
          </button>
          <button
            onClick={() => setView('preview')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              view === 'preview' ? 'bg-white shadow-sm text-indigo-700' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Eye size={14} />
            Preview
          </button>
          <button
            onClick={() => setView('split')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              view === 'split' ? 'bg-white shadow-sm text-indigo-700' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Split
          </button>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 px-2 py-1 border border-gray-200 rounded text-sm">
            <input
              type="text"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              className="w-32 focus:outline-none bg-transparent text-gray-700"
              placeholder="nombre"
            />
            <span className="text-gray-400">.md</span>
          </div>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
          >
            {copied ? <Check size={16} className="text-green-500" /> : <Copy size={16} />}
            {copied ? 'Copiado' : 'Copiar'}
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
          >
            <Download size={16} />
            Descargar
          </button>
        </div>
      </div>

      {/* Content */}
      <div className={`${view === 'split' ? 'grid grid-cols-2 divide-x divide-gray-200' : ''}`} style={{ minHeight: '400px' }}>
        {(view === 'raw' || view === 'split') && (
          <textarea
            value={markdown}
            onChange={(e) => onChange(e.target.value)}
            className="w-full h-full p-4 font-mono text-sm resize-none focus:outline-none bg-white"
            style={{ minHeight: '400px' }}
          />
        )}
        {(view === 'preview' || view === 'split') && (
          <div className="p-4 prose prose-sm max-w-none overflow-auto" style={{ minHeight: '400px' }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {markdown}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
