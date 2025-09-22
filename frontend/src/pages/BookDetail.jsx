import { useEffect, useState, useRef, forwardRef } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Plus, Trash2, BookOpen, FileText, Upload, X, AlertCircle, CheckCircle, Eye, Languages, ChevronLeft, ChevronRight } from 'lucide-react';
import { useBookStore, usePageStore } from '../lib/store';
import { apiClient } from '../lib/api';
import { cn } from '../lib/utils';
import { useModalScrollPrevention } from '../hooks/useModalScrollPrevention';



export default function BookDetail() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const bookId = parseInt(id || '0');
  const initialPage = parseInt(searchParams.get('page') || '1');
  
  const { books, loading: bookLoading, fetchBooks } = useBookStore();
  const { pages, loading: pageLoading, error, fetchPages, deletePage } = usePageStore();
  
  // Refs for auto-scroll functionality
  const pageListRef = useRef(null);
  const pageRefs = useRef({});
  const isManualClick = useRef(false);
  
  // Page selection state
  const [selectedPageNumber, setSelectedPageNumber] = useState(initialPage);
  const [showText, setShowText] = useState(false);
  
  // Modal states
  const [showFileUploadForm, setShowFileUploadForm] = useState(false);
  
  // Translation states
  const [translation, setTranslation] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  const [translationError, setTranslationError] = useState('');
  const [showTranslationModal, setShowTranslationModal] = useState(false);
  
  // File upload states
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadErrors, setUploadErrors] = useState({});
  const [uploadSuccess, setUploadSuccess] = useState([]);
  const [isDragOver, setIsDragOver] = useState(false);
  
  const book = books.find(b => b.id === bookId);
  const bookPages = pages.filter(p => p.book_id === bookId).sort((a, b) => a.page_number - b.page_number);
  const selectedPage = bookPages.find(p => p.page_number === selectedPageNumber);

  useEffect(() => {
    if (books.length === 0) {
      fetchBooks();
    }
    fetchPages(bookId);
  }, [bookId, books.length, fetchBooks, fetchPages]);

  // Update selected page when URL parameter changes
  useEffect(() => {
    const pageParam = parseInt(searchParams.get('page') || '1');
    setSelectedPageNumber(pageParam);
  }, [searchParams]);

  // Set default page to 1 when pages are loaded
  useEffect(() => {
    if (bookPages.length > 0 && !selectedPage) {
      setSelectedPageNumber(1);
    }
  }, [bookPages, selectedPage]);

  // Auto-scroll to selected page in sidebar
  useEffect(() => {
    // Skip auto-scroll if this is a manual click
    if (isManualClick.current) {
      isManualClick.current = false;
      return;
    }
    
    if (selectedPageNumber && bookPages.length > 0 && pageListRef.current) {
      // Add a small delay to ensure DOM elements are rendered
      const scrollToPage = () => {
        const selectedElement = pageRefs.current[selectedPageNumber];
        const container = pageListRef.current;
        
        if (selectedElement && container) {
          // Calculate the position to scroll to center the selected page
          const containerHeight = container.clientHeight;
          const elementTop = selectedElement.offsetTop;
          const elementHeight = selectedElement.clientHeight;
          const scrollTop = elementTop - (containerHeight / 2) + (elementHeight / 2);
          
          container.scrollTo({
            top: Math.max(0, scrollTop),
            behavior: 'smooth'
          });
        } else {
          // If element not found, try again after a short delay
          setTimeout(scrollToPage, 100);
        }
      };
      
      // Use requestAnimationFrame to ensure DOM is updated
      requestAnimationFrame(() => {
        setTimeout(scrollToPage, 50);
      });
    }
  }, [selectedPageNumber, bookPages.length]);

  // Handle ESC key to close modals
  useEffect(() => {
    const handleEscKey = (event) => {
      if (event.key === 'Escape') {
        if (showTranslationModal) {
          setShowTranslationModal(false);
        }
        if (showFileUploadForm) {
          setShowFileUploadForm(false);
        }
      }
    };

    document.addEventListener('keydown', handleEscKey);
    return () => {
      document.removeEventListener('keydown', handleEscKey);
    };
  }, [showTranslationModal, showFileUploadForm]);

  // Prevent background scrolling when modals are open
  useModalScrollPrevention(showTranslationModal || showFileUploadForm);

  // Function to handle page navigation with URL update
  const handlePageSelect = (pageNumber) => {
    isManualClick.current = true;
    setSelectedPageNumber(pageNumber);
    setSearchParams({ page: pageNumber.toString() });
  };



  // Translation function
  const handleTranslate = async () => {
    if (!selectedPage?.id || !selectedPage?.original_text) return;
    
    setIsTranslating(true);
    setTranslationError('');
    setShowTranslationModal(true);
    
    try {
      const response = await apiClient.translateText({
        page_id: selectedPage.id,
        target_language: 'id',
        use_image: true  // Use image-based translation with Gemini
      });

      if (response.success) {
        setTranslation(response.translated_text);
      } else {
        setTranslationError('Translation failed. Please try again.');
      }
    } catch (error) {
      console.error('Translation failed:', error);
      setTranslationError('Translation failed. Please try again.');
    } finally {
      setIsTranslating(false);
    }
  };

  // Navigation functions for translation modal
  const handlePrevPage = () => {
    if (selectedPageNumber > 1) {
      const newPageNumber = selectedPageNumber - 1;
      handlePageSelect(newPageNumber);
      // Clear current translation and error to show the new page's existing translation if any
      setTranslation('');
      setTranslationError('');
    }
  };

  const handleNextPage = () => {
    if (selectedPageNumber < bookPages.length) {
      const newPageNumber = selectedPageNumber + 1;
      handlePageSelect(newPageNumber);
      // Clear current translation and error to show the new page's existing translation if any
      setTranslation('');
      setTranslationError('');
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
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/books"
            className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Books
          </Link>
          <div className="border-l border-gray-300 pl-4">
            <h1 className="text-lg font-semibold text-gray-900">{book.title}</h1>
            <p className="text-sm text-gray-500">by {book.author}</p>
          </div>
        </div>
        <div className="flex space-x-3">
          {/* Only show upload files button if book has no pages */}
          {bookPages.length === 0 && (
            <button
              onClick={() => setShowFileUploadForm(true)}
              className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              <FileText className="w-4 h-4" />
              Upload Files
            </button>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Page Navigation */}
        <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-gray-200 bg-white">
            <h2 className="text-sm font-semibold text-gray-900">Pages ({bookPages.length})</h2>
            {error && (
              <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                {error}
              </div>
            )}
          </div>

          {/* Page List */}
          <div ref={pageListRef} className="flex-1 overflow-y-auto p-3 space-y-2">
            {bookPages.length === 0 ? (
              <div className="p-4 text-center">
                <FileText className="mx-auto h-8 w-8 text-gray-400 mb-2" />
                <p className="text-sm text-gray-500">No pages yet</p>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-500"
                >
                  Add first page
                </button>
              </div>
            ) : (
              <>
                {bookPages.map((page) => (
                  <PageThumbnail
                          key={page.page_number}
                          ref={(el) => pageRefs.current[page.page_number] = el}
                          page={page}
                          isSelected={page.page_number === selectedPageNumber}
                          onClick={() => handlePageSelect(page.page_number)}
                        />
                ))}
              </>
            )}
          </div>
        </div>

        {/* Center Content Area */}
        <div className="flex-1 flex flex-col bg-gray-100">
          {selectedPage ? (
            <>
              {/* Content Header */}
              <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <span className="text-sm font-medium text-gray-900">
                    Page {selectedPage.page_number}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  {/* Translation Button */}
                  {selectedPage.original_text && (
                    <button
                      onClick={handleTranslate}
                      disabled={isTranslating}
                      className="flex items-center gap-2 px-3 py-1 text-sm text-green-600 hover:text-green-500 border border-green-200 rounded-md hover:bg-green-50 disabled:opacity-50"
                    >
                      <Languages className="w-4 h-4" />
                      {isTranslating ? "Translating..." : selectedPage.id_translation ? "Retranslate" : "Translate to Bahasa"}
                    </button>
                  )}
                  
                  {/* Show Translation Button */}
                  {selectedPage.id_translation && (
                    <button
                      onClick={() => setShowTranslationModal(true)}
                      className="flex items-center gap-2 px-3 py-1 text-sm text-blue-600 hover:text-blue-500 border border-blue-200 rounded-md hover:bg-blue-50"
                    >
                      <Eye className="w-4 h-4" />
                      Show Translation
                    </button>
                  )}
                  
                  {/* Show Text/Image Button */}
                  {selectedPage.page_image_url && (
                    <button
                      onClick={() => setShowText(!showText)}
                      className="flex items-center gap-2 px-3 py-1 text-sm text-blue-600 hover:text-blue-500 border border-blue-200 rounded-md hover:bg-blue-50"
                    >
                      <Eye className="w-4 h-4" />
                      {showText ? "Show Image" : "Show Text"}
                    </button>
                  )}
                </div>
              </div>

              {/* Page Content */}
              <div className="flex-1 overflow-auto p-6">
                <PageContent page={selectedPage} showText={showText} />
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <BookOpen className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No page selected</h3>
                <p className="text-sm text-gray-500">
                  {bookPages.length > 0 
                    ? "Select a page from the sidebar to view its content"
                    : "Add pages to this book to get started"
                  }
                </p>
              </div>
            </div>
          )}
        </div>
      </div>





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

      {/* Translation Modal */}
      {showTranslationModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg w-full max-w-6xl h-[90vh] flex flex-col overflow-hidden">
            {/* Left side - Original Text */}
            <div className="flex flex-1 min-h-0">
              <div className="flex-1 flex flex-col border-r border-gray-200">
                <div className="flex items-center justify-between p-6 pb-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Original Text</h3>
                </div>
                <div className="flex-1 p-6 pt-4 overflow-y-auto">
                  {selectedPage?.page_image_url ? (
                    <img
                      src={selectedPage.page_image_url}
                      alt={`Page ${selectedPage.page_number}`}
                      className="w-full h-auto object-contain rounded-lg"
                    />
                  ) : (
                    <div className="text-gray-800 leading-relaxed whitespace-pre-wrap text-sm">
                      {selectedPage?.original_text}
                    </div>
                  )}
                </div>
              </div>

              {/* Right side - Translation */}
              <div className="flex-1 flex flex-col bg-gray-50">
                <div className="flex items-center justify-between p-6 pb-4 border-b border-gray-200">
                  <div className="flex items-center gap-4">
                    <h3 className="text-lg font-semibold text-gray-900">Indonesian Translation</h3>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handlePrevPage}
                        disabled={selectedPageNumber <= 1}
                        className={cn(
                          "p-2 rounded-lg transition-colors",
                          selectedPageNumber <= 1
                            ? "text-gray-300 cursor-not-allowed"
                            : "text-gray-600 hover:text-gray-800 hover:bg-gray-200"
                        )}
                        title="Previous page"
                      >
                        <ChevronLeft className="w-5 h-5" />
                      </button>
                      <span className="text-sm text-gray-500 px-2">
                        Page {selectedPageNumber} of {bookPages.length}
                      </span>
                      <button
                        onClick={handleNextPage}
                        disabled={selectedPageNumber >= bookPages.length}
                        className={cn(
                          "p-2 rounded-lg transition-colors",
                          selectedPageNumber >= bookPages.length
                            ? "text-gray-300 cursor-not-allowed"
                            : "text-gray-600 hover:text-gray-800 hover:bg-gray-200"
                        )}
                        title="Next page"
                      >
                        <ChevronRight className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowTranslationModal(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>

                <div className="flex-1 p-6 pt-4 overflow-y-auto">
                  {isTranslating ? (
                    <div className="flex items-center justify-center h-32">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                      <span className="ml-3 text-gray-600">Translating...</span>
                    </div>
                  ) : translationError ? (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <p className="text-red-800">{translationError}</p>
                      <button
                        onClick={handleTranslate}
                        className="mt-2 text-sm text-red-600 hover:text-red-500 underline"
                      >
                        Try again
                      </button>
                    </div>
                  ) : translation || selectedPage?.id_translation ? (
                    <div 
                      className="text-gray-800 leading-relaxed" 
                      style={{ 
                        fontSize: '14px', 
                        lineHeight: '1.7',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word'
                      }}
                    >
                      {translation || selectedPage?.id_translation}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-32 text-center">
                      <p className="text-gray-500 mb-4">No translation available for this page</p>
                      <button
                        onClick={handleTranslate}
                        className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        <Languages className="w-4 h-4 mr-2" />
                        Translate Page
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// New components for PDF viewer layout
const PageThumbnail = forwardRef(({ page, isSelected, onClick }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "group cursor-pointer p-4 rounded-xl transition-all duration-200 relative",
        isSelected 
          ? "bg-blue-50 border-2 border-blue-300 shadow-md" 
          : "hover:bg-gray-50 hover:shadow-sm border-2 border-transparent"
      )}
      onClick={onClick}
    >
      <div className="flex flex-col items-center space-y-3">
        {/* Page thumbnail */}
        <div className="flex-shrink-0 relative">
          {page.page_image_url ? (
            <img
              src={page.page_image_url}
              alt={`Page ${page.page_number}`}
              className="w-30 h-40 object-cover rounded-lg border-2 border-gray-200 shadow-sm hover:shadow-md transition-shadow"
            />
          ) : (
            <div className="w-30 h-40 bg-gray-100 rounded-lg border-2 border-gray-200 shadow-sm flex items-center justify-center hover:shadow-md transition-shadow">
              <FileText className="w-12 h-12 text-gray-400" />
            </div>
          )}
          
          {/* Translation indicator */}
          {page.id_translation && (
            <div className="absolute -top-2 -right-2 bg-green-500 rounded-full p-1.5 shadow-md">
              <Languages className="w-4 h-4 text-white" />
            </div>
          )}
        </div>

        {/* Page info */}
        <div className="w-full flex items-center justify-center">
          <span className="text-sm font-semibold text-gray-900">
            Page {page.page_number}
          </span>
        </div>
      </div>
    </div>
  );
});

function PageContent({ page, showText }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!page) return null;

  return (
    <div className="max-w-4xl mx-auto">
      {page.page_image_url && !showText ? (
        // Show page image
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <img
            src={page.page_image_url}
            alt={`Page ${page.page_number}`}
            className="w-full h-auto max-h-[80vh] object-contain"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        </div>
      ) : (
        // Show text content
        <div className="bg-white rounded-lg shadow-sm p-6 space-y-6">
          {/* Original Text */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Original Text:</h4>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className={cn(
                "text-sm text-gray-800 leading-relaxed whitespace-pre-wrap",
                !isExpanded && page.original_text.length > 500 && "line-clamp-6"
              )}>
                {page.original_text}
              </p>
              {page.original_text.length > 500 && (
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="text-blue-600 hover:text-blue-500 text-sm mt-2"
                >
                  {isExpanded ? 'Show less' : 'Show more'}
                </button>
              )}
            </div>
          </div>

          {/* English Translation */}
          {page.en_translation && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">English Translation:</h4>
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800 leading-relaxed whitespace-pre-wrap">
                  {page.en_translation}
                </p>
              </div>
            </div>
          )}

          {/* Indonesian Translation */}
          {page.id_translation && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Indonesian Translation:</h4>
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-green-800 leading-relaxed whitespace-pre-wrap">
                  {page.id_translation}
                </p>
              </div>
            </div>
          )}
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