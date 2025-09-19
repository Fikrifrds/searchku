import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Plus, Edit, Trash2, BookOpen, FileText, Upload } from 'lucide-react';
import { useBookStore, usePageStore } from '../lib/store';
import { Book, Page } from '../lib/api';
import { cn } from '../lib/utils';

export default function BookDetail() {
  const { id } = useParams<{ id: string }>();
  const bookId = parseInt(id || '0');
  
  const { books, loading: bookLoading, fetchBooks } = useBookStore();
  const { pages, loading: pageLoading, error, fetchPages, deletePage } = usePageStore();
  
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  
  const book = books.find(b => b.id === bookId);
  const bookPages = pages.filter(p => p.book_id === bookId);

  useEffect(() => {
    if (books.length === 0) {
      fetchBooks();
    }
    fetchPages(bookId);
  }, [bookId, books.length, fetchBooks, fetchPages]);

  const handleDeletePage = async (pageNumber: number) => {
    if (window.confirm('Are you sure you want to delete this page?')) {
      await deletePage(bookId, pageNumber);
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
    </div>
  );
}

interface PageCardProps {
  page: Page;
  onDelete: () => void;
}

function PageCard({ page, onDelete }: PageCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-500">Page {page.page_number}</span>
            {page.embedding_model && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Indexed
              </span>
            )}
          </div>
          
          <div className="mt-2">
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
            <div className="mt-3 p-3 bg-gray-50 rounded">
              <p className="text-sm text-gray-600 font-medium">Translation:</p>
              <p className="text-gray-700 mt-1">{page.translated_text}</p>
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
        
        <div className="flex space-x-2 ml-4">
          <button
            onClick={onDelete}
            className="text-red-600 hover:text-red-500"
            title="Delete page"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

interface CreatePageModalProps {
  bookId: number;
  onClose: () => void;
}

function CreatePageModal({ bookId, onClose }: CreatePageModalProps) {
  const { createPage, loading } = usePageStore();
  const [formData, setFormData] = useState({
    page_number: 1,
    original_text: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
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

interface UploadCoverModalProps {
  bookId: number;
  onClose: () => void;
}

function UploadCoverModal({ bookId, onClose }: UploadCoverModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const { fetchBooks } = useBookStore();

  const handleSubmit = async (e: React.FormEvent) => {
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