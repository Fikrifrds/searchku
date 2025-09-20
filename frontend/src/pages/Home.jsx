import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Search, Upload, Plus, TrendingUp, FileText, Zap } from 'lucide-react';
import { useBookStore, usePageStore, useSearchStore } from '../lib/store';
import { cn } from '../lib/utils';

export default function Home() {
  const { books, fetchBooks } = useBookStore();
  const { pages, fetchAllPages } = usePageStore();
  const { results } = useSearchStore();
  const [recentBooks, setRecentBooks] = useState([]);

  useEffect(() => {
    fetchBooks();
    fetchAllPages();
  }, [fetchBooks, fetchAllPages]);

  useEffect(() => {
    // Get 3 most recent books
    const sorted = [...books]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 3);
    setRecentBooks(sorted);
  }, [books]);

  const totalPages = pages.length;
  const indexedPages = pages.filter(page => page.embedding_model).length;
  const indexingProgress = totalPages > 0 ? (indexedPages / totalPages) * 100 : 0;

  const quickActions = [
    {
      name: 'Add New Book',
      description: 'Create a new book in your collection',
      href: '/books',
      icon: Plus,
      color: 'bg-blue-600 hover:bg-blue-700',
    },
    {
      name: 'Search Content',
      description: 'Find content across all your books',
      href: '/search',
      icon: Search,
      color: 'bg-green-600 hover:bg-green-700',
    },
    {
      name: 'Upload Files',
      description: 'Bulk upload and process text files',
      href: '/upload',
      icon: Upload,
      color: 'bg-purple-600 hover:bg-purple-700',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900">Welcome to SearchKu</h1>
        <p className="mt-4 text-xl text-gray-600">
          Your intelligent digital book processing and search platform
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BookOpen className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Books</dt>
                  <dd className="text-lg font-medium text-gray-900">{books.length}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FileText className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Pages</dt>
                  <dd className="text-lg font-medium text-gray-900">{totalPages}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Zap className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Indexed Pages</dt>
                  <dd className="text-lg font-medium text-gray-900">{indexedPages}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Search Ready</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {Math.round(indexingProgress)}%
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Indexing Progress */}
      {totalPages > 0 && indexingProgress < 100 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <Zap className="h-5 w-5 text-yellow-600 mr-2" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-yellow-800">
                Semantic Indexing in Progress
              </h3>
              <p className="text-sm text-yellow-700 mt-1">
                {indexedPages} of {totalPages} pages have been processed for semantic search
              </p>
              <div className="mt-2 bg-yellow-200 rounded-full h-2">
                <div
                  className="bg-yellow-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${indexingProgress}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.name}
                to={action.href}
                className="group relative bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-blue-500 rounded-lg shadow hover:shadow-md transition-shadow"
              >
                <div>
                  <span className={cn(
                    'rounded-lg inline-flex p-3 text-white',
                    action.color
                  )}>
                    <Icon className="h-6 w-6" />
                  </span>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-900 group-hover:text-blue-600">
                    {action.name}
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    {action.description}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Recent Books */}
      {recentBooks.length > 0 && (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Recent Books</h2>
            <Link
              to="/books"
              className="text-blue-600 hover:text-blue-500 text-sm font-medium"
            >
              View all books →
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {recentBooks.map((book) => (
              <Link
                key={book.id}
                to={`/books/${book.id}`}
                className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      {book.cover_image_url ? (
                        <img
                          src={book.cover_image_url}
                          alt={book.title}
                          className="h-16 w-12 object-cover rounded"
                        />
                      ) : (
                        <div className="h-16 w-12 bg-gray-200 rounded flex items-center justify-center">
                          <BookOpen className="h-6 w-6 text-gray-400" />
                        </div>
                      )}
                    </div>
                    <div className="ml-4 flex-1">
                      <h3 className="text-lg font-medium text-gray-900 truncate">
                        {book.title}
                      </h3>
                      <p className="text-sm text-gray-500 truncate">{book.author}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(book.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Getting Started */}
      {books.length === 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">
          <BookOpen className="mx-auto h-12 w-12 text-blue-600 mb-4" />
          <h3 className="text-lg font-medium text-blue-900 mb-2">
            Get Started with SearchKu
          </h3>
          <p className="text-blue-700 mb-6">
            Create your first book to begin building your digital library with semantic search capabilities.
          </p>
          <Link
            to="/books"
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create Your First Book
          </Link>
        </div>
      )}
    </div>
  );
}