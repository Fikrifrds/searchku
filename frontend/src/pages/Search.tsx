import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search as SearchIcon, BookOpen, FileText, Zap, Filter } from 'lucide-react';
import { useSearchStore, useBookStore } from '../lib/store';
import { SearchResult } from '../lib/api';
import { cn } from '../lib/utils';

export default function Search() {
  const { results, loading, error, semanticSearch, textSearch, clearResults } = useSearchStore();
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<'semantic' | 'text'>('semantic');
  const [filters, setFilters] = useState({
    bookId: '',
    language: ''
  });
  const [showFilters, setShowFilters] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const searchParams = {
      query: query.trim(),
      limit: 20,
      book_id: filters.bookId ? parseInt(filters.bookId) : undefined,
      language: filters.language || undefined
    };

    if (searchType === 'semantic') {
      await semanticSearch(searchParams);
    } else {
      await textSearch(searchParams);
    }
  };

  const handleClearSearch = () => {
    setQuery('');
    clearResults();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Search Books</h1>
        <p className="mt-2 text-gray-600">
          Find content across your digital book collection using semantic or text search
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white shadow rounded-lg p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          {/* Search Type Toggle */}
          <div className="flex justify-center">
            <div className="inline-flex rounded-md shadow-sm" role="group">
              <button
                type="button"
                onClick={() => setSearchType('semantic')}
                className={cn(
                  'px-4 py-2 text-sm font-medium border rounded-l-lg focus:z-10 focus:ring-2 focus:ring-blue-500',
                  searchType === 'semantic'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
                )}
              >
                <Zap className="w-4 h-4 mr-2 inline" />
                Semantic Search
              </button>
              <button
                type="button"
                onClick={() => setSearchType('text')}
                className={cn(
                  'px-4 py-2 text-sm font-medium border rounded-r-lg focus:z-10 focus:ring-2 focus:ring-blue-500',
                  searchType === 'text'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
                )}
              >
                <SearchIcon className="w-4 h-4 mr-2 inline" />
                Text Search
              </button>
            </div>
          </div>

          {/* Search Input */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <SearchIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder={searchType === 'semantic' 
                ? "Search by meaning and context (e.g., 'love and relationships')" 
                : "Search for exact text matches (e.g., 'specific phrase')"
              }
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
            />
            <div className="absolute inset-y-0 right-0 flex items-center">
              <button
                type="button"
                onClick={() => setShowFilters(!showFilters)}
                className="mr-3 p-1 text-gray-400 hover:text-gray-600"
                title="Filters"
              >
                <Filter className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Book ID (optional)
                </label>
                <input
                  type="number"
                  placeholder="Filter by specific book ID"
                  value={filters.bookId}
                  onChange={(e) => setFilters({ ...filters, bookId: e.target.value })}
                  className="block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Language (optional)
                </label>
                <select
                  value={filters.language}
                  onChange={(e) => setFilters({ ...filters, language: e.target.value })}
                  className="block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All languages</option>
                  <option value="en">English</option>
                  <option value="id">Indonesian</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="zh">Chinese</option>
                  <option value="ja">Japanese</option>
                </select>
              </div>
            </div>
          )}

          {/* Search Button */}
          <div className="flex justify-center space-x-3">
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Searching...
                </>
              ) : (
                <>
                  <SearchIcon className="w-5 h-5 mr-2" />
                  Search
                </>
              )}
            </button>
            {(query || results.length > 0) && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Clear
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Search Type Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            {searchType === 'semantic' ? (
              <Zap className="h-5 w-5 text-blue-600" />
            ) : (
              <SearchIcon className="h-5 w-5 text-blue-600" />
            )}
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              {searchType === 'semantic' ? 'Semantic Search' : 'Text Search'}
            </h3>
            <p className="text-sm text-blue-700 mt-1">
              {searchType === 'semantic'
                ? 'Finds content based on meaning and context, even if exact words don\'t match. Great for discovering related concepts and ideas.'
                : 'Finds exact text matches within the content. Use quotes for exact phrases or specific terms.'}
            </p>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">
              Search Results ({results.length})
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Found {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
            </p>
          </div>
          <div className="divide-y divide-gray-200">
            {results.map((result, index) => (
              <SearchResultCard key={index} result={result} />
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {!loading && query && results.length === 0 && (
        <div className="text-center py-12">
          <SearchIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search terms or switching between semantic and text search
          </p>
        </div>
      )}

      {/* Empty State */}
      {!query && results.length === 0 && (
        <div className="text-center py-12">
          <BookOpen className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Start searching</h3>
          <p className="mt-1 text-sm text-gray-500">
            Enter a search query above to find content across your book collection
          </p>
        </div>
      )}
    </div>
  );
}

interface SearchResultCardProps {
  result: SearchResult;
}

function SearchResultCard({ result }: SearchResultCardProps) {
  return (
    <div className="p-6 hover:bg-gray-50">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <Link
              to={`/books/${result.book_id}`}
              className="text-lg font-medium text-blue-600 hover:text-blue-500"
            >
              {result.book_title}
            </Link>
            <span className="text-sm text-gray-500">by {result.book_author}</span>
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-gray-500 mb-3">
            <span className="flex items-center">
              <FileText className="w-4 h-4 mr-1" />
              Page {result.page_number}
            </span>
            <span>Language: {result.book_language}</span>
            {result.similarity_score && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                {Math.round(result.similarity_score * 100)}% match
              </span>
            )}
          </div>
          
          <div className="space-y-3">
            {result.snippet && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Relevant excerpt:</p>
                <p className="text-gray-900 bg-yellow-50 p-3 rounded border-l-4 border-yellow-400">
                  {result.snippet}
                </p>
              </div>
            )}
            
            {result.original_text && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Original text:</p>
                <p className="text-gray-700 line-clamp-3">
                  {result.original_text}
                </p>
              </div>
            )}
            
            {result.translated_text && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Translation:</p>
                <p className="text-gray-700 bg-gray-50 p-3 rounded">
                  {result.translated_text}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}