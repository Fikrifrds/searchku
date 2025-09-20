import { useState, useEffect } from 'react';
import { Search as SearchIcon, Filter, X, Book } from 'lucide-react';
import { useBookStore } from '../lib/store';
import { apiClient } from '../lib/api';
import { cn } from '../lib/utils';



export default function Search() {
  const { books } = useBookStore();
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedBookId, setSelectedBookId] = useState(null);
  const [searchType, setSearchType] = useState('semantic');
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setIsSearching(true);
    try {
      const searchRequest = {
        query: query.trim(),
        limit: 20,
        similarity_threshold: 0.8
      };
      
      let response;
      if (searchType === 'semantic') {
        response = await apiClient.semanticSearch(searchRequest);
      } else {
        response = await apiClient.textSearch(searchRequest);
      }
      
      // Filter by selected book if specified
      let results = response.results;
      if (selectedBookId) {
        results = results.filter(result => result.book.id === selectedBookId);
      }
      
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const clearSearch = () => {
    setQuery('');
    setSearchResults([]);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Search Books</h1>
        <p className="mt-2 text-gray-600">
          Search through your book collection using semantic or text-based search
        </p>
      </div>


      {/* Search Interface */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="space-y-4">
          {/* Search Input */}
          <div className="relative">
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search for content in your books..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Search Options */}
          <div className="flex flex-wrap items-center gap-4">
            {/* Search Type */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Search Type:</label>
              <select
                value={searchType}
                onChange={(e) => setSearchType(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="semantic">Semantic Search</option>
                <option value="text">Text Search</option>
              </select>
            </div>

            {/* Book Filter */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Filter by Book:</label>
              <select
                value={selectedBookId || ''}
                onChange={(e) => setSelectedBookId(e.target.value ? Number(e.target.value) : null)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Books</option>
                {books.map((book) => (
                  <option key={book.id} value={book.id}>
                    {book.title} - {book.author}
                  </option>
                ))}
              </select>
            </div>

            {/* Search Button */}
            <button
              onClick={handleSearch}
              disabled={!query.trim() || isSearching}
              className={cn(
                'px-4 py-2 rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2',
                query.trim() && !isSearching
                  ? 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              )}
            >
              {isSearching ? 'Searching...' : 'Search'}
            </button>

            {/* Clear Button */}
            {(query || searchResults.length > 0) && (
              <button
                onClick={clearSearch}
                className="px-4 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-800 focus:outline-none"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">
              Search Results ({searchResults.length})
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Found {searchResults.length} results for "{query}"
            </p>
          </div>
          <div className="divide-y divide-gray-200">
            {searchResults.map((result, index) => (
              <SearchResultCard key={`${result.page.id}-${index}`} result={result} />
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {query && !isSearching && searchResults.length === 0 && (
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <SearchIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search query or search type
          </p>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-800 mb-3">Search Tips</h3>
        <ul className="list-disc list-inside space-y-2 text-sm text-blue-700">
          <li><strong>Semantic Search:</strong> Finds content based on meaning and context</li>
          <li><strong>Text Search:</strong> Finds exact text matches in your books</li>
          <li>Use the book filter to search within specific books</li>
          <li>Try different keywords if you don't find what you're looking for</li>
        </ul>
      </div>
    </div>
  );
}

function SearchResultCard({ result }) {
  const { page, book, similarity_score, snippet } = result;
  
  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Book Info */}
          <div className="flex items-center space-x-2 mb-2">
            <Book className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-900">{book.title}</span>
            <span className="text-sm text-gray-500">by {book.author}</span>
            <span className="text-sm text-gray-400">• Page {page.page_number}</span>
          </div>
          
          {/* Content Preview */}
          <div className="mt-2">
            <p className="text-sm text-gray-700 line-clamp-3">
              {snippet || page.original_text.substring(0, 200) + (page.original_text.length > 200 ? '...' : '')}
            </p>
          </div>
          
          {/* Translation if available */}
          {page.translated_text && (
            <div className="mt-3 p-3 bg-gray-50 rounded-md">
              <p className="text-xs font-medium text-gray-500 mb-1">Translation:</p>
              <p className="text-sm text-gray-700 line-clamp-2">
                {page.translated_text.substring(0, 150) + (page.translated_text.length > 150 ? '...' : '')}
              </p>
            </div>
          )}
        </div>
        
        {/* Similarity Score */}
        {similarity_score && (
          <div className="ml-4 flex-shrink-0">
            <div className="text-xs text-gray-500">Relevance</div>
            <div className="text-sm font-medium text-gray-900">
              {(similarity_score * 100).toFixed(1)}%
            </div>
          </div>
        )}
      </div>
    </div>
  );
}