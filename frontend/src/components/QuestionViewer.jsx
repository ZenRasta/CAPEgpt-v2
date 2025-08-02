import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

function QuestionViewer() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [question, setQuestion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [imageLoaded, setImageLoaded] = useState(false);

  useEffect(() => {
    if (!id) {
      setError('Question ID is required');
      setLoading(false);
      return;
    }

    fetchQuestion();
  }, [id]);

  const fetchQuestion = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/questions/${id}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Question not found');
        }
        throw new Error(`Failed to fetch question: ${response.status}`);
      }

      const questionData = await response.json();
      setQuestion(questionData);
    } catch (err) {
      console.error('Error fetching question:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderProcessingStatus = () => {
    if (!question) return null;

    const statusConfig = {
      'pending': { 
        color: 'text-yellow-600', 
        bg: 'bg-yellow-100 border-yellow-300',
        icon: '⏳',
        message: 'Processing... 🚀'
      },
      'processing': { 
        color: 'text-blue-600', 
        bg: 'bg-blue-100 border-blue-300',
        icon: '🔄',
        message: 'Processing with Mathpix... ✨'
      },
      'completed': { 
        color: 'text-green-600', 
        bg: 'bg-green-100 border-green-300',
        icon: '✅',
        message: 'Processing complete! 🎉'
      },
      'failed': { 
        color: 'text-red-600', 
        bg: 'bg-red-100 border-red-300',
        icon: '❌',
        message: 'Processing failed 😔'
      }
    };

    const config = statusConfig[question.processing_status] || statusConfig['pending'];

    return (
      <div className={`px-4 py-3 rounded-xl border-2 ${config.bg} ${config.color} text-sm mb-6 font-semibold`}>
        <span className="mr-2 text-lg">{config.icon}</span>
        {config.message}
      </div>
    );
  };

  const renderQuestionContent = () => {
    if (!question || question.processing_status !== 'completed') {
      return null;
    }

    // If no processed content available, show fallback message
    if (!question.mathpix_markdown && !question.mathpix_svg) {
      return (
        <div className="bg-white rounded-2xl p-8 border-2 border-gray-200 shadow-xl">
          <p className="text-gray-600 text-center text-lg">
            📸 No processed content available. The original image is shown above.
          </p>
        </div>
      );
    }

    // Render SVG if available and preferred
    if (question.uses_svg && question.mathpix_svg) {
      return (
        <div className="bg-white rounded-2xl p-8 border-2 border-blue-200 shadow-xl">
          <div className="text-sm text-blue-600 mb-4 flex items-center gap-2 font-semibold">
            <span>🎨</span>
            <span>Pixel-perfect rendering (SVG) ✨</span>
          </div>
          <div 
            className="overflow-auto max-h-96 bg-gray-50 p-6 rounded-xl border border-gray-200"
            dangerouslySetInnerHTML={{ __html: question.mathpix_svg }}
          />
        </div>
      );
    }

    // Render Markdown with KaTeX
    if (question.mathpix_markdown) {
      return (
        <div className="bg-white rounded-2xl p-8 border-2 border-green-200 shadow-xl">
          <div className="text-sm text-green-600 mb-4 flex items-center gap-2 font-semibold">
            <span>📝</span>
            <span>Mathematical notation (Markdown + KaTeX) 🔥</span>
          </div>
          <div className="prose prose-lg max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkMath]}
              rehypePlugins={[rehypeKatex]}
            >
              {question.mathpix_markdown}
            </ReactMarkdown>
          </div>
        </div>
      );
    }

    return null;
  };

  const renderMetadata = () => {
    if (!question) return null;

    return (
      <div className="bg-white rounded-2xl p-8 border-2 border-gray-200 shadow-xl space-y-6">
        <h3 className="text-2xl font-bold text-gray-800 gradient-text">Question Details 📊</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-blue-50 p-4 rounded-xl border border-blue-200">
            <span className="text-blue-600 font-semibold text-sm uppercase tracking-wide">Subject:</span>
            <p className="text-blue-800 font-bold text-lg mt-1">{question.subject || 'Unknown'} 🎓</p>
          </div>
          
          <div className="bg-purple-50 p-4 rounded-xl border border-purple-200">
            <span className="text-purple-600 font-semibold text-sm uppercase tracking-wide">Uploaded:</span>
            <p className="text-purple-800 font-bold text-lg mt-1">
              {new Date(question.created_at).toLocaleDateString()} 📅
            </p>
          </div>
        </div>

        {question.topics && question.topics.length > 0 && (
          <div className="bg-yellow-50 p-4 rounded-xl border border-yellow-200">
            <span className="text-yellow-600 font-semibold text-sm uppercase tracking-wide mb-3 block">Topics:</span>
            <div className="flex flex-wrap gap-2">
              {question.topics.map((topic, index) => (
                <span 
                  key={index}
                  className="px-3 py-1 bg-yellow-200 text-yellow-800 rounded-full text-sm font-semibold border border-yellow-300"
                >
                  🏷️ {topic}
                </span>
              ))}
            </div>
          </div>
        )}

        {question.mathpix_confidence !== undefined && (
          <div className="bg-green-50 p-4 rounded-xl border border-green-200">
            <span className="text-green-600 font-semibold text-sm uppercase tracking-wide">Processing Confidence:</span>
            <div className="flex items-center gap-2 mt-2">
              <div className="bg-green-200 h-3 rounded-full flex-1 overflow-hidden">
                <div 
                  className="bg-green-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.round(question.mathpix_confidence * 100)}%` }}
                ></div>
              </div>
              <span className="text-green-800 font-bold text-lg">
                {Math.round(question.mathpix_confidence * 100)}% 🎯
              </span>
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 font-['Poppins',sans-serif]">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="spinner mx-auto mb-4"></div>
              <p className="text-gray-600 text-lg font-semibold">Loading question... 🚀</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 font-['Poppins',sans-serif]">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center max-w-md mx-auto">
            <div className="bg-white rounded-2xl p-8 shadow-xl border-2 border-red-200">
              <h1 className="text-3xl font-bold text-red-600 mb-4">❌ Oops!</h1>
              <p className="text-gray-700 mb-6 text-lg">{error}</p>
              <button
                onClick={() => navigate('/')}
                className="bg-blue-600 text-white px-8 py-4 rounded-full font-bold text-lg hover:bg-blue-700 transition shadow-lg"
              >
                ← Back to Home 🏠
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 font-['Poppins',sans-serif]">
      {/* Header */}
      <header className="bg-blue-600 text-white sticky top-0 z-10 shadow-md">
        <nav className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold gradient-text">CAPE·GPT 🚀</h1>
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-white hover:text-blue-200 transition-colors font-semibold"
          >
            <span>←</span>
            <span>Back to Home 🏠</span>
          </button>
        </nav>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Page Title */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2 gradient-text">
            Question Viewer 📖
          </h1>
          <p className="text-xl text-gray-600">
            {question?.original_filename || 'Loading question...'} ✨
          </p>
        </div>

        {/* Processing Status */}
        {renderProcessingStatus()}

        {/* Original Image Reference */}
        {question?.signed_url && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2 gradient-text">
              <span>📷</span>
              Original Image
            </h2>
            <div className="bg-white rounded-2xl p-6 border-2 border-gray-200 shadow-xl">
              <img
                src={question.signed_url}
                alt={question.original_filename}
                className={`max-w-full h-auto rounded-xl border-2 border-gray-300 shadow-lg transition-opacity duration-300 ${
                  imageLoaded ? 'opacity-100' : 'opacity-50'
                }`}
                onLoad={() => setImageLoaded(true)}
                onError={() => setImageLoaded(false)}
              />
              {!imageLoaded && (
                <div className="text-gray-500 text-center mt-4 font-semibold">
                  Loading original image... ⏳
                </div>
              )}
            </div>
          </div>
        )}

        {/* Processed Content */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2 gradient-text">
            <span>🔍</span>
            Processed Content
          </h2>
          {renderQuestionContent()}
        </div>

        {/* Question Metadata */}
        {renderMetadata()}

        {/* Action Buttons */}
        <div className="mt-8 text-center space-x-4">
          <button
            onClick={() => navigate('/')}
            className="bg-blue-600 text-white px-8 py-4 rounded-full font-bold text-lg hover:bg-blue-700 transition shadow-lg"
          >
            🏠 Back to Home
          </button>
          <button
            onClick={() => window.location.reload()}
            className="bg-green-600 text-white px-8 py-4 rounded-full font-bold text-lg hover:bg-green-700 transition shadow-lg"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-blue-600 text-white py-6 mt-8">
        <div className="container mx-auto px-4 text-center">
          <p>&copy; 2025 CAPE·GPT. All rights reserved. Made with ❤️ by Gen Alpha Vibes!</p>
        </div>
      </footer>
    </div>
  );
}

export default QuestionViewer;