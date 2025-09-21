import { useState, useEffect } from 'react';
import { Search as SearchIcon, Book, X, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useBookStore } from '../lib/store';
import { apiClient } from '../lib/api';
import { cn } from '../lib/utils';

export default function Search() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { books, fetchBooks } = useBookStore();
  
  // Initialize state from URL parameters
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedBookId, setSelectedBookId] = useState(
    searchParams.get('book') ? parseInt(searchParams.get('book')) : null
  );
  const [searchType, setSearchType] = useState('multilingual'); // Always default to multilingual
  const [isSearching, setIsSearching] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(
    searchParams.get('page') ? parseInt(searchParams.get('page')) : 1
  );
  const [totalResults, setTotalResults] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const resultsPerPage = 20;

  // Fetch books on component mount
  useEffect(() => {
    fetchBooks();
  }, [fetchBooks]);

  // Perform search on page load if query exists in URL
  useEffect(() => {
    const performInitialSearch = async () => {
      if (!query.trim()) return;

      setIsSearching(true);
      try {
        const detectedLanguage = detectLanguage(query);
        const offset = (currentPage - 1) * resultsPerPage;
        const searchRequest = {
          query: query.trim(),
          limit: resultsPerPage,
          offset: offset,
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
        setTotalResults(response.total_results);
        setHasMore(response.has_more);
      } catch (error) {
        console.error('Search failed:', error);
        setSearchResults([]);
        setTotalResults(0);
        setHasMore(false);
      } finally {
        setIsSearching(false);
      }
    };

    performInitialSearch();
  }, [currentPage]); // Re-run when page changes

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

  const handleSearch = async (pageNumber = 1) => {
    if (!query.trim()) return;

    // Reset to page 1 for new searches, or use specified page
    const targetPage = pageNumber;
    setCurrentPage(targetPage);

    // Update URL parameters
    const params = new URLSearchParams();
    params.set('q', query.trim());
    params.set('page', targetPage.toString());
    if (selectedBookId) {
      params.set('book', selectedBookId.toString());
    }
    setSearchParams(params);

    setIsSearching(true);
    try {
      const detectedLanguage = detectLanguage(query);
      const offset = (targetPage - 1) * resultsPerPage;
      const searchRequest = {
        query: query.trim(),
        limit: resultsPerPage,
        offset: offset,
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
      setTotalResults(response.total_results);
      setHasMore(response.has_more);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
      setTotalResults(0);
      setHasMore(false);
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
    setCurrentPage(1);
    setTotalResults(0);
    setHasMore(false);
    setSearchParams({}); // Clear URL parameters
  };

  const handleBookFilterChange = (bookId) => {
    const newBookId = bookId ? Number(bookId) : null;
    setSelectedBookId(newBookId);
    // Reset to page 1 when changing book filter
    setCurrentPage(1);
    // Update URL if there's an active search
    if (query.trim()) {
      const params = new URLSearchParams();
      params.set('q', query.trim());
      params.set('page', '1');
      if (newBookId) {
        params.set('book', newBookId.toString());
      }
      setSearchParams(params);
      // Trigger new search with updated filter
      handleSearch(1);
    }
  };

  // Pagination handlers
  const handlePageChange = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages && !isSearching) {
      handleSearch(pageNumber);
    }
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      handlePageChange(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (hasMore) {
      handlePageChange(currentPage + 1);
    }
  };

  // Calculate total pages
  const totalPages = Math.ceil(totalResults / resultsPerPage);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Search Books</h1>
        <p className="mt-2 text-gray-600">
          Search through your Arabic book collection
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
            {/* Book Filter */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Filter by Book:</label>
              <select
                value={selectedBookId || ''}
                onChange={(e) => handleBookFilterChange(e.target.value)}
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
              Search Results ({totalResults} total, showing {searchResults.length} on page {currentPage})
            </h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {searchResults.map((result, index) => (
                <SearchResultCard key={`${result.page_id}-${index}`} result={result} navigate={navigate} />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Pagination */}
      {searchResults.length > 0 && totalPages > 1 && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-sm text-gray-700">
              <span>
                Showing {((currentPage - 1) * resultsPerPage) + 1} to {Math.min(currentPage * resultsPerPage, totalResults)} of {totalResults} results
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              {/* Previous Button */}
              <button
                onClick={handlePreviousPage}
                disabled={currentPage === 1 || isSearching}
                className={cn(
                  'flex items-center px-3 py-2 text-sm font-medium rounded-md',
                  currentPage === 1 || isSearching
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                )}
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Previous
              </button>

              {/* Page Numbers */}
              <div className="flex items-center space-x-1">
                {/* First page */}
                {currentPage > 3 && (
                  <>
                    <button
                      onClick={() => handlePageChange(1)}
                      disabled={isSearching}
                      className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-md"
                    >
                      1
                    </button>
                    {currentPage > 4 && (
                      <span className="px-2 py-2 text-sm text-gray-500">...</span>
                    )}
                  </>
                )}

                {/* Current page and neighbors */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }

                  if (pageNum < 1 || pageNum > totalPages) return null;

                  return (
                    <button
                      key={pageNum}
                      onClick={() => handlePageChange(pageNum)}
                      disabled={isSearching}
                      className={cn(
                        'px-3 py-2 text-sm font-medium rounded-md',
                        pageNum === currentPage
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                      )}
                    >
                      {pageNum}
                    </button>
                  );
                })}

                {/* Last page */}
                {currentPage < totalPages - 2 && (
                  <>
                    {currentPage < totalPages - 3 && (
                      <span className="px-2 py-2 text-sm text-gray-500">...</span>
                    )}
                    <button
                      onClick={() => handlePageChange(totalPages)}
                      disabled={isSearching}
                      className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-md"
                    >
                      {totalPages}
                    </button>
                  </>
                )}
              </div>

              {/* Next Button */}
              <button
                onClick={handleNextPage}
                disabled={!hasMore || isSearching}
                className={cn(
                  'flex items-center px-3 py-2 text-sm font-medium rounded-md',
                  !hasMore || isSearching
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                )}
              >
                Next
                <ChevronRight className="w-4 h-4 ml-1" />
              </button>
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
    </div>
  );
}

function SearchResultCard({ result, navigate }) {
  const [showText, setShowText] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [translation, setTranslation] = useState(null);
  const [isTranslating, setIsTranslating] = useState(false);
  const [showTranslation, setShowTranslation] = useState(false);
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

  const handleGoToDetail = () => {
    navigate(`/books/${book_id}?page=${page_number}`);
  };

  const handleTranslate = async () => {
    if (!page_id || isTranslating) return;

    setIsTranslating(true);
    try {
      const response = await apiClient.translateText({
        page_id: page_id,
        target_language: 'id',
        use_image: true  // Use image-based translation with Gemini
      });

      if (response.success) {
        setTranslation(response.translated_text);
        setShowTranslation(true);
      }
    } catch (error) {
      console.error('Translation failed:', error);
    } finally {
      setIsTranslating(false);
    }
  };

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

            {/* Similarity Score */}
            {similarity_score && (
              <div className="mt-2">
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  {(similarity_score * 100).toFixed(1)}% match
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-3 flex items-center space-x-2">
          {page_image_url && (
            <button
              onClick={() => setShowText(!showText)}
              className="text-sm text-blue-600 hover:text-blue-500 font-medium px-3 py-1 rounded-md border border-blue-200 hover:bg-blue-50"
            >
              {showText ? "Show Image" : "Show Text"}
            </button>
          )}
          {id_translation && (
            <button
              onClick={() => setShowTranslation(!showTranslation)}
              className="text-sm text-purple-600 hover:text-purple-500 font-medium px-3 py-1 rounded-md border border-purple-200 hover:bg-purple-50"
            >
              {showTranslation ? "Hide Translation" : "Show Translation"}
            </button>
          )}
          <button
            onClick={handleGoToDetail}
            className="text-sm text-green-600 hover:text-green-500 font-medium px-3 py-1 rounded-md border border-green-200 hover:bg-green-50 flex items-center space-x-1"
          >
            <ExternalLink className="w-3 h-3" />
            <span>Go to Detail</span>
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="p-4">
        {page_image_url && !showText ? (
          // Show large image preview
          <div className="bg-gray-50 rounded-lg overflow-hidden">
            <img
              src={page_image_url}
              alt={`Page ${page_number} from ${book_title}`}
              className="w-full h-auto min-h-[500px] max-h-[800px] object-contain cursor-zoom-in hover:scale-105 transition-transform duration-200"
              onError={(e) => {
                e.target.style.display = 'none';
                setShowText(true);
              }}
              onClick={() => setShowModal(true)}
            />
          </div>
        ) : (
          // Show full text content
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Original Text:</h4>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                  {original_text}
                </p>
              </div>
            </div>

            {/* English Translation if available */}
            {en_translation && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">English Translation:</h4>
                <div className="p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-800 leading-relaxed whitespace-pre-wrap">
                    {en_translation}
                  </p>
                </div>
              </div>
            )}

            {/* Indonesian Translation if available */}
            {id_translation && showTranslation && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Indonesian Translation:</h4>
                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-green-800 leading-relaxed whitespace-pre-wrap">
                    {id_translation}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Image Modal */}
      {showModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={() => setShowModal(false)}
        >
          <div 
            className="relative max-w-7xl max-h-full"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="absolute top-4 right-4 flex items-center space-x-2 z-10">
              {!id_translation && (
                <button
                  onClick={handleTranslate}
                  disabled={isTranslating}
                  className="text-white hover:text-gray-300 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-3 py-2 rounded-md text-sm font-medium"
                >
                  {isTranslating ? 'Translating...' : 'Translate to Bahasa'}
                </button>
              )}
              <button
                onClick={() => setShowModal(false)}
                className="text-white hover:text-gray-300 bg-black bg-opacity-50 rounded-full p-2"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="flex gap-6 max-w-full max-h-[90vh]">
               {/* Image section */}
               <div className="flex-1">
                 <img
                   src={page_image_url}
                   alt={`Page ${page_number} from ${book_title}`}
                   className="w-full h-auto max-h-[90vh] object-contain rounded-lg shadow-lg"
                   onClick={(e) => e.stopPropagation()}
                 />
               </div>
               
               {/* Translation section - side by side */}
                {(translation || id_translation) && (
                  <div className="flex-1 bg-white border border-gray-200 rounded-lg p-6 max-h-[90vh] overflow-y-auto shadow-sm">
                    <div className="mb-4">
                      <h4 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                        Terjemahan Bahasa Indonesia
                      </h4>
                    </div>
                    
                    <div 
                       className="text-gray-800 leading-relaxed" 
                       style={{ 
                         fontSize: '14px', 
                         lineHeight: '1.7',
                         whiteSpace: 'pre-wrap',
                         wordBreak: 'break-word'
                       }}
                     >
                       {(translation || id_translation)}
                     </div>
                    
                    <button
                      onClick={() => setTranslation(null)}
                      className="mt-6 px-4 py-2 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700 transition-colors"
                    >
                      Tutup Terjemahan
                    </button>
                  </div>
                )}
             </div>
          </div>
        </div>
      )}
    </div>
  );
}