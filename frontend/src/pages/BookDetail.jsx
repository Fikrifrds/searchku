import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Plus, Trash2, BookOpen, FileText, Upload, X, AlertCircle, CheckCircle } from 'lucide-react';
import { useBookStore, usePageStore } from '../lib/store';

import { cn } from '../lib/utils';

export default function BookDetail() {
  const { id } = useParams();
  const bookId = parseInt(id || '0');
  
  const { books, loading: bookLoading, fetchBooks } = useBookStore();
  const { pages, loading: pageLoading, error, fetchPages, deletePage } = usePageStore();
  
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [showFileUploadForm, setShowFileUploadForm] = useState(false);
  
  // File upload states
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadErrors, setUploadErrors] = useState({});
  const [uploadSuccess, setUploadSuccess] = useState([]);
  const [isDragOver, setIsDragOver] = useState(false);
  
  const book = books.find(b => b.id === bookId);
  const bookPages = pages.filter(p => p.book_id === bookId);

  useEffect(() => {
    if (books.length === 0) {
      fetchBooks();
    }
    fetchPages(bookId);
  }, [bookId, books.length, fetchBooks, fetchPages]);

  const handleDeletePage = async (pageNumber) => {
    if (window.confirm('Are you sure you want to delete this page?')) {
      await deletePage(bookId, pageNumber);
    }
  };

  // File upload handlers
  const handleFileSelect = (files) => {
    if (!files) return;
    
    const validFiles = Array.from(files).filter(file => {
      const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
      return validTypes.includes(file.type) || file.name.toLowerCase().endsWith('.pdf') || file.name.toLowerCase().endsWith('.doc') || file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.txt');
    });
    
    setSelectedFiles(prev => [...prev, ...validFiles]);
    setUploadErrors({});
    setUploadSuccess([]);
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const uploadFiles = async () => {
    if (selectedFiles.length === 0) return;
    
    setIsUploading(true);
    setUploadErrors({});
    setUploadSuccess([]);
    
    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('files', file);
    });
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/books/${bookId}/upload-files`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Upload failed');
      }
      
      await response.json();
      setUploadSuccess(selectedFiles.map(f => f.name));
      setSelectedFiles([]);
      
      // Refresh pages list
      await fetchPages(bookId);
    } catch (error) {
      console.error('Upload failed:', error);
      const errorMsg = error instanceof Error ? error.message : 'Upload failed';
      const errors = {};
      selectedFiles.forEach(file => {
        errors[file.name] = errorMsg;
      });
      setUploadErrors(errors);
    } finally {
      setIsUploading(false);
    }
  };

  if (bookLoading || pageLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="text-center py-12">
        <BookOpen className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Book not found</h3>
        <p className="mt-1 text-sm text-gray-500">The book you're looking for doesn't exist.</p>
        <div className="mt-6">
          <Link
            to="/books"
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Books
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/books"
            className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Books
          </Link>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowUploadForm(true)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload Cover
          </button>
          <button
            onClick={() => setShowFileUploadForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <FileText className="w-4 h-4" />
            Upload Files
          </button>
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Page
          </button>
        </div>
      </div>

      {/* Book Info */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4">
          <div className="flex items-start space-x-6">
            <div className="flex-shrink-0">
              {book.cover_image_url ? (
                <img
                  src={book.cover_image_url}
                  alt={book.title}
                  className="w-32 h-40 object-cover rounded-lg shadow"
                />
              ) : (
                <div className="w-32 h-40 bg-gray-200 rounded-lg flex items-center justify-center">
                  <BookOpen className="h-12 w-12 text-gray-400" />
                </div>
              )}
            </div>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900">{book.title}</h1>
              <p className="text-lg text-gray-600 mt-1">by {book.author}</p>
              <p className="text-sm text-gray-500 mt-1">Language: {book.language}</p>
              {book.description && (
                <p className="text-gray-700 mt-4">{book.description}</p>
              )}
              <div className="mt-4 flex items-center space-x-4 text-sm text-gray-500">
                <span>{bookPages.length} pages</span>
                <span>Created: {new Date(book.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Pages */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Pages</h2>
        </div>
        <div className="p-6">
          {bookPages.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No pages yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by adding the first page to this book
              </p>
              <div className="mt-6">
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Page
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {bookPages
                .sort((a, b) => a.page_number - b.page_number)
                .map((page) => (
                  <PageCard
                    key={page.page_number}
                    page={page}
                    onDelete={() => handleDeletePage(page.page_number)}
                  />
                ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Page Modal */}
      {showCreateForm && (
        <CreatePageModal
          bookId={bookId}
          onClose={() => setShowCreateForm(false)}
        />
      )}

      {/* Upload Cover Modal */}
      {showUploadForm && (
        <UploadCoverModal
          bookId={bookId}
          onClose={() => setShowUploadForm(false)}
        />
      )}

      {/* File Upload Modal */}
      {showFileUploadForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 -top-6">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Upload Files to {book?.title}</h2>
              <button
                onClick={() => setShowFileUploadForm(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Drag and Drop Area */}
            <div
              className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
                isDragOver ? "border-blue-500 bg-blue-50" : "border-gray-300"
              )}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-700 mb-2">
                Drag and drop files here, or click to select
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Supported formats: PDF, DOC, DOCX, TXT
              </p>
              <input
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.txt,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                onChange={(e) => handleFileSelect(e.target.files)}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
              >
                Select Files
              </label>
            </div>

            {/* Selected Files */}
            {selectedFiles.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-medium mb-3">Selected Files ({selectedFiles.length})</h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {selectedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-blue-600" />
                        <div>
                          <p className="font-medium text-sm">{file.name}</p>
                          <p className="text-xs text-gray-500">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="text-red-500 hover:text-red-700"
                        disabled={isUploading}
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Upload Errors */}
            {Object.keys(uploadErrors).length > 0 && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  <h4 className="font-medium text-red-800">Upload Errors</h4>
                </div>
                <div className="space-y-1">
                  {Object.entries(uploadErrors).map(([filename, error]) => (
                    <p key={filename} className="text-sm text-red-700">
                      <span className="font-medium">{filename}:</span> {error}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Upload Success */}
            {uploadSuccess.length > 0 && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <h4 className="font-medium text-green-800">Successfully Uploaded</h4>
                </div>
                <div className="space-y-1">
                  {uploadSuccess.map((filename) => (
                    <p key={filename} className="text-sm text-green-700">
                      {filename}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Smart Processing Info */}
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-blue-800">Smart Processing Enabled</h4>
                  <p className="text-xs text-blue-700 mt-1">
                    Files will be automatically processed using the best method for each page:
                  </p>
                  <ul className="text-xs text-blue-700 mt-2 space-y-1 list-disc list-inside">
                    <li>Text extraction for pages with selectable text</li>
                    <li>OCR for image-only pages automatically</li>
                    <li>Mixed processing for documents with both types</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Upload Button */}
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setShowFileUploadForm(false)}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                disabled={isUploading}
              >
                Cancel
              </button>
              <button
                onClick={uploadFiles}
                disabled={selectedFiles.length === 0 || isUploading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {isUploading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Upload Files
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PageCard({ page, onDelete }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showText, setShowText] = useState(false);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-sm transition-shadow">
      <div className="flex justify-between items-start p-4 pb-0">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-500">Page {page.page_number}</span>
          {page.embedding_model && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Indexed
            </span>
          )}
          {page.page_image_url && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Has Image
            </span>
          )}
        </div>

        <div className="flex space-x-2">
          {page.page_image_url && (
            <button
              onClick={() => setShowText(!showText)}
              className="text-gray-600 hover:text-gray-500 text-xs"
              title={showText ? "Show image" : "Show text"}
            >
              {showText ? "Show Image" : "Show Text"}
            </button>
          )}
          <button
            onClick={onDelete}
            className="text-red-600 hover:text-red-500"
            title="Delete page"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="p-4 pt-2">
        {page.page_image_url && !showText ? (
          // Show page image if available and not in text mode
          <div className="space-y-3">
            <div className="bg-gray-100 rounded-lg overflow-hidden">
              <img
                src={page.page_image_url}
                alt={`Page ${page.page_number}`}
                className="w-full h-auto max-h-96 object-contain"
                onError={(e) => {
                  e.target.style.display = 'none';
                  setShowText(true);
                }}
              />
            </div>
            {page.original_text && (
              <div className="text-center">
                <p className="text-xs text-gray-500">
                  Text available - click "Show Text" to view
                </p>
              </div>
            )}
          </div>
        ) : (
          // Show text content
          <div className="space-y-3">
            <div>
              <p className={cn(
                "text-gray-700",
                !isExpanded && "line-clamp-3"
              )}>
                {page.original_text}
              </p>
              {page.original_text.length > 200 && (
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="text-blue-600 hover:text-blue-500 text-sm mt-1"
                >
                  {isExpanded ? 'Show less' : 'Show more'}
                </button>
              )}
            </div>

            {page.translated_text && (
              <div className="p-3 bg-gray-50 rounded">
                <p className="text-sm text-gray-600 font-medium">Translation:</p>
                <p className="text-gray-700 mt-1">{page.translated_text}</p>
              </div>
            )}
          </div>
        )}

        <div className="mt-3 text-xs text-gray-500">
          Created: {new Date(page.created_at).toLocaleDateString()}
          {page.updated_at !== page.created_at && (
            <span className="ml-2">
              Updated: {new Date(page.updated_at).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function CreatePageModal({ bookId, onClose }) {
  const { createPage, loading } = usePageStore();
  const [formData, setFormData] = useState({
    page_number: 1,
    original_text: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await createPage(bookId, formData);
      onClose();
    } catch (error) {
      // Error is handled by the store
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Page</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Page Number</label>
              <input
                type="number"
                min="1"
                required
                value={formData.page_number}
                onChange={(e) => setFormData({ ...formData, page_number: parseInt(e.target.value) })}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Original Text</label>
              <textarea
                required
                value={formData.original_text}
                onChange={(e) => setFormData({ ...formData, original_text: e.target.value })}
                rows={6}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter the original text for this page..."
              />
            </div>
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Page'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function UploadCoverModal({ bookId, onClose }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const { fetchBooks } = useBookStore();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`/api/books/${bookId}/cover`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        await fetchBooks(); // Refresh books to get updated cover URL
        onClose();
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Upload Cover Image</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Cover Image</label>
              <input
                type="file"
                accept="image/*"
                required
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={uploading || !file}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}