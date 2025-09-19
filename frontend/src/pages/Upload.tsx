import { useState } from 'react';
import { Upload as UploadIcon, FileText, BookOpen, AlertCircle, CheckCircle, X } from 'lucide-react';
import { useBookStore, usePageStore } from '../lib/store';
import { cn } from '../lib/utils';
import { Book } from '../lib/api';

interface UploadItem {
  id: string;
  file: File;
  status: 'pending' | 'processing' | 'success' | 'error';
  progress: number;
  error?: string;
  bookId?: number;
  pagesCreated?: number;
}

export default function Upload() {
  const { books, fetchBooks } = useBookStore();
  const { createPage } = usePageStore();
  const [uploadItems, setUploadItems] = useState<UploadItem[]>([]);
  const [selectedBookId, setSelectedBookId] = useState<number | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    handleFiles(files);
  };

  const handleFiles = (files: File[]) => {
    const textFiles = files.filter(file => 
      file.type === 'text/plain' || 
      file.name.endsWith('.txt') ||
      file.name.endsWith('.md')
    );

    const newItems: UploadItem[] = textFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      status: 'pending',
      progress: 0
    }));

    setUploadItems(prev => [...prev, ...newItems]);
  };

  const removeUploadItem = (id: string) => {
    setUploadItems(prev => prev.filter(item => item.id !== id));
  };

  const processFile = async (item: UploadItem, bookId: number): Promise<void> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = async (e) => {
        try {
          const content = e.target?.result as string;
          
          // Split content into pages (simple approach: split by double newlines or every 1000 chars)
          const pages = splitIntoPages(content);
          
          let createdPages = 0;
          
          for (let i = 0; i < pages.length; i++) {
            const pageContent = pages[i].trim();
            if (pageContent) {
              try {
                await createPage(bookId, {
                  page_number: i + 1,
                  original_text: pageContent
                });
                createdPages++;
                
                // Update progress
                const progress = ((i + 1) / pages.length) * 100;
                setUploadItems(prev => prev.map(uploadItem => 
                  uploadItem.id === item.id 
                    ? { ...uploadItem, progress, pagesCreated: createdPages }
                    : uploadItem
                ));
              } catch (error) {
                console.error(`Error creating page ${i + 1}:`, error);
              }
            }
          }
          
          resolve();
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(item.file);
    });
  };

  const splitIntoPages = (content: string): string[] => {
    // Split by double newlines first (paragraph breaks)
    let pages = content.split(/\n\s*\n/);
    
    // If pages are too long, split them further
    const maxPageLength = 2000; // characters
    const finalPages: string[] = [];
    
    pages.forEach(page => {
      if (page.length <= maxPageLength) {
        finalPages.push(page);
      } else {
        // Split long pages by sentences or at word boundaries
        const sentences = page.split(/[.!?]+/);
        let currentPage = '';
        
        sentences.forEach(sentence => {
          if ((currentPage + sentence).length <= maxPageLength) {
            currentPage += sentence + '.';
          } else {
            if (currentPage) {
              finalPages.push(currentPage.trim());
            }
            currentPage = sentence + '.';
          }
        });
        
        if (currentPage) {
          finalPages.push(currentPage.trim());
        }
      }
    });
    
    return finalPages.filter(page => page.trim().length > 0);
  };

  const startProcessing = async () => {
    if (!selectedBookId) {
      alert('Please select a book first');
      return;
    }

    const pendingItems = uploadItems.filter(item => item.status === 'pending');
    
    for (const item of pendingItems) {
      setUploadItems(prev => prev.map(uploadItem => 
        uploadItem.id === item.id 
          ? { ...uploadItem, status: 'processing', bookId: selectedBookId }
          : uploadItem
      ));

      try {
        await processFile(item, selectedBookId);
        
        setUploadItems(prev => prev.map(uploadItem => 
          uploadItem.id === item.id 
            ? { ...uploadItem, status: 'success', progress: 100 }
            : uploadItem
        ));
      } catch (error) {
        setUploadItems(prev => prev.map(uploadItem => 
          uploadItem.id === item.id 
            ? { 
                ...uploadItem, 
                status: 'error', 
                error: error instanceof Error ? error.message : 'Unknown error'
              }
            : uploadItem
        ));
      }
    }
  };

  const clearCompleted = () => {
    setUploadItems(prev => prev.filter(item => 
      item.status !== 'success' && item.status !== 'error'
    ));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Upload & Process Files</h1>
        <p className="mt-2 text-gray-600">
          Upload text files to automatically create book pages with semantic indexing
        </p>
      </div>

      {/* Book Selection */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Select Target Book</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {books.map(book => (
            <div
              key={book.id}
              onClick={() => setSelectedBookId(book.id)}
              className={cn(
                'p-4 border rounded-lg cursor-pointer transition-colors',
                selectedBookId === book.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              <div className="flex items-center space-x-3">
                <BookOpen className="h-8 w-8 text-gray-400" />
                <div>
                  <h3 className="font-medium text-gray-900">{book.title}</h3>
                  <p className="text-sm text-gray-500">{book.author}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
        {books.length === 0 && (
          <p className="text-gray-500 text-center py-4">
            No books available. Create a book first before uploading files.
          </p>
        )}
      </div>

      {/* File Upload Area */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Upload Text Files</h2>
        
        <div
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <UploadIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            Drop files here or click to upload
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Supports .txt and .md files up to 10MB each
          </p>
          <input
            type="file"
            multiple
            accept=".txt,.md,text/plain"
            onChange={handleFileInput}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
          >
            <UploadIcon className="w-4 h-4 mr-2" />
            Choose Files
          </label>
        </div>
      </div>

      {/* Upload Queue */}
      {uploadItems.length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-medium text-gray-900">
              Upload Queue ({uploadItems.length})
            </h2>
            <div className="flex space-x-3">
              <button
                onClick={startProcessing}
                disabled={!selectedBookId || uploadItems.every(item => item.status !== 'pending')}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Process Files
              </button>
              <button
                onClick={clearCompleted}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Clear Completed
              </button>
            </div>
          </div>
          
          <div className="divide-y divide-gray-200">
            {uploadItems.map(item => (
              <UploadItemCard
                key={item.id}
                item={item}
                onRemove={() => removeUploadItem(item.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 mb-2">How it works</h3>
        <ol className="list-decimal list-inside space-y-2 text-blue-800">
          <li>Select a target book where the pages will be created</li>
          <li>Upload one or more text files (.txt or .md format)</li>
          <li>Files will be automatically split into pages based on content structure</li>
          <li>Each page will be processed to generate semantic embeddings for search</li>
          <li>Pages will be added to the selected book with automatic numbering</li>
        </ol>
      </div>
    </div>
  );
}

interface UploadItemCardProps {
  item: UploadItem;
  onRemove: () => void;
}

function UploadItemCard({ item, onRemove }: UploadItemCardProps) {
  const getStatusIcon = () => {
    switch (item.status) {
      case 'pending':
        return <FileText className="h-5 w-5 text-gray-400" />;
      case 'processing':
        return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />;
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
    }
  };

  const getStatusColor = () => {
    switch (item.status) {
      case 'pending':
        return 'text-gray-600';
      case 'processing':
        return 'text-blue-600';
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
    }
  };

  return (
    <div className="p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3 flex-1">
          {getStatusIcon()}
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-900">{item.file.name}</p>
            <p className="text-xs text-gray-500">
              {(item.file.size / 1024).toFixed(1)} KB
            </p>
          </div>
          <div className="text-right">
            <p className={cn('text-sm font-medium', getStatusColor())}>
              {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
            </p>
            {item.pagesCreated && (
              <p className="text-xs text-gray-500">
                {item.pagesCreated} pages created
              </p>
            )}
          </div>
        </div>
        
        <button
          onClick={onRemove}
          className="ml-4 text-gray-400 hover:text-gray-600"
          title="Remove from queue"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      
      {item.status === 'processing' && (
        <div className="mt-2">
          <div className="bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${item.progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">{Math.round(item.progress)}% complete</p>
        </div>
      )}
      
      {item.error && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
          <p className="text-sm text-red-800">{item.error}</p>
        </div>
      )}
    </div>
  );
}