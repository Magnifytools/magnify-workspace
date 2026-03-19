import { useState, useCallback } from 'react';
import { Upload, FileText, Image, Table, Globe, File, Loader2 } from 'lucide-react';
import { convertFile } from '../lib/api';

const FILE_ICONS = {
  pdf: FileText,
  docx: FileText,
  txt: FileText,
  html: Globe,
  htm: Globe,
  csv: Table,
  png: Image,
  jpg: Image,
  jpeg: Image,
  webp: Image,
};

const ACCEPTED = '.pdf,.docx,.png,.jpg,.jpeg,.webp,.html,.htm,.txt,.csv';

export default function FileUploader({ onResult, onError }) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState('');

  const handleFile = useCallback(async (file) => {
    if (!file) return;
    setFileName(file.name);
    setLoading(true);
    onError('');

    try {
      const result = await convertFile(file);
      onResult(result.markdown);
    } catch (err) {
      onError(err.message);
      onResult('');
    } finally {
      setLoading(false);
    }
  }, [onResult, onError]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    handleFile(file);
  }, [handleFile]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragging(false), []);

  const handleInput = useCallback((e) => {
    handleFile(e.target.files?.[0]);
  }, [handleFile]);

  const ext = fileName.split('.').pop()?.toLowerCase();
  const IconComp = FILE_ICONS[ext] || File;

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${
        dragging
          ? 'border-indigo-500 bg-indigo-50'
          : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
      }`}
      onClick={() => document.getElementById('file-input').click()}
    >
      <input
        id="file-input"
        type="file"
        accept={ACCEPTED}
        onChange={handleInput}
        className="hidden"
      />

      {loading ? (
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="animate-spin text-indigo-500" size={40} />
          <p className="text-gray-600">Convirtiendo <strong>{fileName}</strong>...</p>
        </div>
      ) : fileName ? (
        <div className="flex flex-col items-center gap-3">
          <IconComp className="text-indigo-500" size={40} />
          <p className="text-gray-700"><strong>{fileName}</strong> convertido</p>
          <p className="text-sm text-gray-400">Arrastra otro archivo o haz clic para cambiar</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <Upload className="text-gray-400" size={40} />
          <p className="text-gray-600 font-medium">Arrastra un archivo aquí o haz clic para seleccionar</p>
          <p className="text-sm text-gray-400">
            PDF, DOCX, PNG, JPG, HTML, TXT, CSV (máx. 20MB)
          </p>
        </div>
      )}
    </div>
  );
}
