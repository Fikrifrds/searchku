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
  const [searchType, setSearchType] = useState('multilingual');
  const [isSearching, setIsSearching] = useState(false);

  // Simple language detection
  const detectLanguage = (text) => {
    const trimmedText = text.trim().toLowerCase();

    // Indonesian words
    const indonesianWords = ['dan', 'atau', 'yang', 'di', 'ke', 'dari', 'untuk', 'dengan', 'pada', 'adalah', 'tentang', 'hadis', 'niat', 'puasa', 'sholat'];
    // English words
    const englishWords = ['the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about', 'intention', 'prayer', 'fasting'];

    const words = trimmedText.split(/\s+/);
    let indonesianCount = 0;
    let englishCount = 0;

    words.forEach(word => {
      if (indonesianWords.includes(word)) indonesianCount++;
      if (englishWords.includes(word)) englishCount++;
    });

    if (indonesianCount > englishCount) return 'id';
    if (englishCount > indonesianCount) return 'en';
    return 'auto'; // Default to auto-detection
  };

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const detectedLanguage = detectLanguage(query);
      const searchRequest = {
        query: query.trim(),
        limit: 20,
        similarity_threshold: searchType === 'multilingual' ? 0.1 : 0.1,
        query_language: detectedLanguage
      };

      let response;
      if (searchType === 'multilingual') {
        response = await apiClient.multilingualSearch(searchRequest);
      } else if (searchType === 'semantic') {
        response = await apiClient.semanticSearch(searchRequest);
      } else {
        response = await apiClient.textSearch(searchRequest);
      }

      // Filter by selected book if specified
      let results = response.results;
      if (selectedBookId) {
        results = results.filter(result => result.book_id === selectedBookId);
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
          Search through your Arabic book collection using English, Bahasa Indonesia, or Arabic queries
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
                <option value="multilingual">Multilingual Search (Recommended)</option>
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
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {searchResults.map((result, index) => (
                <SearchResultCard key={`${result.page_id}-${index}`} result={result} />
              ))}
            </div>
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
          <li><strong>Multilingual Search (Recommended):</strong> Search Arabic content using English or Bahasa Indonesia. Automatically detects your query language and finds relevant Arabic text.</li>
          <li><strong>Semantic Search:</strong> Finds content based on meaning and context in the same language</li>
          <li><strong>Text Search:</strong> Finds exact text matches in your books</li>
          <li>Use the book filter to search within specific books</li>
          <li><strong>Language Detection:</strong> The system automatically detects if you're searching in English, Bahasa Indonesia, or Arabic</li>
          <li>Try queries like "hadis tentang niat" or "hadith about intention" to find Arabic content</li>
        </ul>
      </div>
    </div>
  );
}

function SearchResultCard({ result }) {
  const [showText, setShowText] = useState(false);
  const {
    page_id,
    book_id,
    page_number,
    original_text,
    en_translation,
    id_translation,
    page_image_url,
    similarity_score,
    snippet,
    book_title,
    book_author
  } = result;

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow bg-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            {/* Book Info */}
            <div className="flex items-center space-x-2 mb-1">
              <Book className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <span className="text-sm font-medium text-gray-900 truncate">{book_title}</span>
            </div>
            <div className="text-xs text-gray-500">
              by {book_author} • Page {page_number}
            </div>

            {/* Badges */}
            <div className="flex items-center space-x-2 mt-2">
              {page_image_url && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  Has Image
                </span>
              )}
              {similarity_score && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  {(similarity_score * 100).toFixed(1)}% match
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Toggle Button for Image/Text */}
        {page_image_url && (
          <div className="mt-3">
            <button
              onClick={() => setShowText(!showText)}
              className="text-xs text-blue-600 hover:text-blue-500 font-medium"
            >
              {showText ? "👁️ Show Image" : "📝 Show Text"}
            </button>
          </div>
        )}
      </div>

      {/* Content Area */}
      <div className="p-4">
        {page_image_url && !showText ? (
          // Show image preview
          <div className="bg-gray-50 rounded-lg overflow-hidden">
            <img
              src={page_image_url}
              alt={`Page ${page_number} from ${book_title}`}
              className="w-full h-auto max-h-80 object-contain"
              onError={(e) => {
                e.target.style.display = 'none';
                setShowText(true);
              }}
            />
          </div>
        ) : (
          // Show text content
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-700 line-clamp-4 leading-relaxed">
                {snippet || original_text.substring(0, 300) + (original_text.length > 300 ? '...' : '')}
              </p>
            </div>

            {/* Translation if available */}
            {(en_translation || id_translation) && (
              <div className="p-3 bg-blue-50 rounded-md">
                <p className="text-xs font-medium text-blue-700 mb-1">Translation:</p>
                <p className="text-sm text-blue-800 line-clamp-3 leading-relaxed">
                  {(en_translation || id_translation).substring(0, 200) + ((en_translation || id_translation).length > 200 ? '...' : '')}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}