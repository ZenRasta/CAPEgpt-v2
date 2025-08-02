import { useState, useRef, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { ChevronDown } from 'lucide-react';
import QuestionViewer from './components/QuestionViewer';
import 'katex/dist/katex.min.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

function MainApp() {
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [textQuery, setTextQuery] = useState('');
  const [subject, setSubject] = useState('Pure Mathematics');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [expandedInsights, setExpandedInsights] = useState(new Set());
  const [popularQuestions, setPopularQuestions] = useState([]);
  const [currentSection, setCurrentSection] = useState('home');
  
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const subjects = [
    'Pure Mathematics',
    'Applied Mathematics', 
    'Physics',
    'Chemistry'
  ];

  // Fetch popular questions on component mount
  useEffect(() => {
    fetchPopularQuestions();
  }, []);

  const fetchPopularQuestions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/popular-questions?subject=Pure Mathematics&limit=6`);
      if (response.ok) {
        const data = await response.json();
        setPopularQuestions(data.popular_questions || []);
      }
    } catch (error) {
      console.error('Failed to fetch popular questions:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const getProbabilityBadge = (probabilities) => {
    if (!probabilities || Object.keys(probabilities).length === 0) {
      return { label: 'Unknown', color: 'bg-gray-500/20 text-gray-300', emoji: '❓' };
    }
    
    const values = Object.values(probabilities);
    if (values.includes('High')) {
      return { label: 'High', color: 'bg-red-500/20 text-red-300 border-red-500/30', emoji: '🔥', percentage: '80%' };
    } else if (values.includes('Medium')) {
      return { label: 'Medium', color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30', emoji: '⚖️', percentage: '50%' };
    } else {
      return { label: 'Low', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30', emoji: '🧊', percentage: '20%' };
    }
  };

  const toggleInsights = (messageIndex) => {
    const newExpanded = new Set(expandedInsights);
    if (newExpanded.has(messageIndex)) {
      newExpanded.delete(messageIndex);
    } else {
      newExpanded.add(messageIndex);
    }
    setExpandedInsights(newExpanded);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (file) => {
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
      setError('Image too large (max 10MB)');
      return;
    }

    setImage(file);
    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target.result);
    reader.readAsDataURL(file);
    setError(null);
  };

  const clearImage = () => {
    setImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (isImage = false) => {
    if (loading) return;
    
    console.log('Submit clicked:', { isImage, hasImage: !!image, textQuery });
    console.log('Image file:', image ? { name: image.name, type: image.type, size: image.size } : null);
    
    setLoading(true);
    setError(null);
    
    try {
      let text = textQuery.trim();
      
      if (isImage && image) {
        console.log('Starting image upload...');
        // Upload image and get OCR text
        const formData = new FormData();
        formData.append('file', image);
        
        console.log('Sending request to:', `${API_BASE_URL}/upload`);
        const ocrRes = await fetch(`${API_BASE_URL}/upload`, {
          method: 'POST',
          body: formData
        });
        
        console.log('Upload response status:', ocrRes.status);
        
        if (!ocrRes.ok) {
          const errorData = await ocrRes.json();
          console.error('Upload error:', errorData);
          throw new Error(errorData.detail || 'Failed to process image');
        }
        
        const ocrData = await ocrRes.json();
        console.log('OCR result:', ocrData);
        text = ocrData.text;
        
        if (!text.trim()) {
          throw new Error('No text could be extracted from the image');
        }
      }
      
      if (!text) {
        setError('Please enter a question or upload an image');
        return;
      }

      // Add user message
      const userMessage = {
        type: 'user',
        content: text,
        timestamp: new Date(),
        hasImage: isImage && image
      };
      setMessages(prev => [...prev, userMessage]);

      // Query the API
      const queryRes = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, subject })
      });

      if (!queryRes.ok) {
        const errorData = await queryRes.json();
        throw new Error(errorData.detail || 'Failed to get response');
      }

      const data = await queryRes.json();
      
      // Add bot response
      const botMessage = {
        type: 'bot',
        content: data,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);

      // Clear inputs
      setTextQuery('');
      clearImage();
      
    } catch (err) {
      console.error('Error:', err);
      setError(err.message);
      
      // Add error message to chat
      const errorMessage = {
        type: 'error',
        content: err.message,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-100 text-gray-800 min-h-screen font-poppins">
      {/* Header */}
      <header className="bg-blue-600 text-white sticky top-0 z-10 shadow-md">
        <nav className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-white">CAPE·GPT 🚀</h1>
          <ul className="flex space-x-4">
            <li><a href="#home" onClick={(e) => { e.preventDefault(); setCurrentSection('home'); }} className="hover:underline">Home 🏠</a></li>
            <li><a href="#upload" onClick={(e) => { e.preventDefault(); setCurrentSection('upload'); }} className="hover:underline">Upload 📸</a></li>
            <li><a href="#popular" onClick={(e) => { e.preventDefault(); setCurrentSection('popular'); }} className="hover:underline">Popular 🔥</a></li>
            <li><a href="#scoreboard" onClick={(e) => { e.preventDefault(); setCurrentSection('scoreboard'); }} className="hover:underline">Scoreboard 🏆</a></li>
          </ul>
        </nav>
      </header>

      {/* Hero Section */}
      {currentSection === 'home' && (
        <>
          <section className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white py-20">
            <div className="container mx-auto px-4 text-center">
              <h2 className="text-5xl font-bold mb-4 text-white bounce">Your AI Buddy for CAPE Exams! 💥</h2>
              <p className="text-xl mb-6">Snap questions, get lit solutions, and level up your game! 🎮</p>
              <button 
                onClick={() => setCurrentSection('upload')}
                className="bg-white text-blue-600 px-8 py-4 rounded-full font-bold text-lg hover:bg-gray-200 transition shadow-lg"
              >
                Let's Go! 🚀
              </button>
            </div>
          </section>

          {/* Quick Examples */}
          <section className="container mx-auto px-4 py-12">
            <h3 className="text-3xl font-bold mb-6 text-center text-blue-600">Quick Vibes Examples 🤩</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-8 rounded-2xl shadow-xl fade-in hover:scale-105 transition">
                <p className="font-bold text-lg">Differentiate f(x) = x²eˣ 📐</p>
                <button className="mt-4 text-blue-600 hover:underline font-semibold">View Solution ✨</button>
              </div>
              <div className="bg-white p-8 rounded-2xl shadow-xl fade-in hover:scale-105 transition">
                <p className="font-bold text-lg">Projectile Motion: Max Height 🚀</p>
                <button className="mt-4 text-blue-600 hover:underline font-semibold">View Solution ✨</button>
              </div>
            </div>
          </section>
        </>
      )}

      {/* File Upload Section */}
      {currentSection === 'upload' && (
        <>
          <section className="bg-gray-200 py-12 min-h-screen">
            <div className="container mx-auto px-4">
              <h3 className="text-3xl font-bold mb-6 text-center text-blue-600">Drop Your Question 📸</h3>
              
              {messages.length === 0 && (
                <div className="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-xl mb-8">
                  <div 
                    className={`border-2 border-dashed p-8 rounded-xl text-center transition-colors ${
                      dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                    }`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                  >
                    <p className="text-center mb-4 text-lg">Snap a past-paper question (PNG/JPG/PDF) or click to upload! 🖼️</p>
                    <div className="flex justify-center mb-4">
                      <label className="bg-blue-600 text-white px-8 py-4 rounded-full cursor-pointer hover:bg-blue-700 transition font-bold">
                        Choose File 📂
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept="image/*"
                          onChange={(e) => e.target.files[0] && handleFileSelect(e.target.files[0])}
                          className="hidden"
                        />
                      </label>
                    </div>
                    {image && (
                      <p className="text-center text-sm text-gray-600">
                        📸 {image.name} ({(image.size / 1024).toFixed(1)}KB)
                      </p>
                    )}
                  </div>
                </div>
              )}

            {/* Subject Selection */}
            <div className="max-w-md mx-auto mb-8">
              <label className="block text-center text-lg font-semibold mb-4">Choose Your Subject 🎓</label>
              <select 
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full p-4 rounded-full border-2 border-blue-300 focus:border-blue-600 focus:outline-none text-center font-semibold"
              >
                {subjects.map(subj => (
                  <option key={subj} value={subj}>
                    {subj === 'Pure Mathematics' ? 'Math 📊' : 
                     subj === 'Applied Mathematics' ? 'Additional Math 📈' : 
                     subj === 'Physics' ? 'Physics ⚡' :
                     'Chemistry 🧪'}
                  </option>
                ))}
              </select>
            </div>

            {/* Text Input - for direct text queries */}
            <div className="max-w-md mx-auto mb-8">
              <textarea
                value={textQuery}
                onChange={(e) => setTextQuery(e.target.value)}
                placeholder="...or paste the OCR'd text here and ask anything! 💭"
                rows="4"
                className="w-full p-4 border-2 border-gray-300 rounded-xl focus:border-blue-600 focus:outline-none"
              />
            </div>

            {/* Submit Button */}
            <div className="max-w-md mx-auto text-center">
              <button 
                onClick={() => handleSubmit(image ? true : false)}
                disabled={loading}
                className="bg-blue-600 text-white px-8 py-4 rounded-full font-bold text-lg hover:bg-blue-700 transition shadow-lg disabled:bg-gray-400"
              >
                {loading ? 'Processing... ⏳' : 'Send 🚀'}
              </button>
            </div>

            {/* Error Display */}
            {error && (
              <div className="max-w-md mx-auto mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-xl text-center">
                ❌ {error}
              </div>
            )}

            {/* Messages Display */}
            {messages.length > 0 && (
              <div className="max-w-4xl mx-auto mt-8">
                {messages.map((msg, idx) => (
                  <div key={idx} className="mb-6">
                    {msg.type === 'user' && (
                      <div className="bg-blue-600 text-white p-4 rounded-xl max-w-lg ml-auto">
                        <p className="font-semibold">You asked:</p>
                        <p>{msg.content}</p>
                      </div>
                    )}
                    
                    {msg.type === 'bot' && (
                      <div className="bg-white p-6 rounded-xl shadow-lg max-w-4xl">
                        <p className="font-bold text-lg mb-4 text-blue-600">🤖 CAPE·GPT Solution</p>
                        <div className="prose max-w-none">
                          <ReactMarkdown
                            remarkPlugins={[remarkMath]}
                            rehypePlugins={[rehypeKatex]}
                          >
                            {msg.content.answer}
                          </ReactMarkdown>
                        </div>
                        
                        {(msg.content.years?.length > 0 || msg.content.topics?.length > 0 || msg.content.probabilities) && (() => {
                          const badge = getProbabilityBadge(msg.content.probabilities);
                          const isExpanded = expandedInsights.has(idx);
                          
                          return (
                            <div className="border border-gray-300 rounded-xl overflow-hidden mt-4">
                              <button 
                                className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium bg-gray-100 hover:bg-gray-200 transition"
                                onClick={() => toggleInsights(idx)}
                              >
                                <span className="flex items-center gap-3">
                                  <span className="text-gray-800">Exam Insights 📊</span>
                                  <span className={`text-xs px-2 py-1 rounded border ${badge.color}`}>
                                    {badge.emoji} {badge.label} • {badge.percentage}
                                  </span>
                                </span>
                                <ChevronDown 
                                  className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                />
                              </button>
                              
                              {isExpanded && (
                                <div className="px-4 py-3 text-sm space-y-4 bg-gray-50">
                                  {msg.content.years?.length > 0 ? (
                                    <div>
                                      <div className="text-gray-600 uppercase text-xs mb-2 tracking-wide">Appeared in</div>
                                      <div className="flex flex-wrap gap-2">
                                        {msg.content.years.slice(0, 8).map(year => (
                                          <span key={year} className="px-2 py-1 rounded bg-blue-100 text-blue-800 text-xs font-medium border border-blue-200">
                                            {year}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  ) : (
                                    <div>
                                      <div className="text-gray-600 uppercase text-xs mb-2 tracking-wide">Appeared in</div>
                                      <p className="text-gray-500 text-sm italic">No historical data found. This may be a new or rare question type.</p>
                                    </div>
                                  )}
                                  
                                  {msg.content.topics?.length > 0 ? (
                                    <div>
                                      <div className="text-gray-600 uppercase text-xs mb-2 tracking-wide">Syllabus objectives</div>
                                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                                        {msg.content.topics.map((topic, topicIdx) => (
                                          <li key={topicIdx} className="text-sm leading-relaxed">
                                            {topic}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  ) : (
                                    <div>
                                      <div className="text-gray-600 uppercase text-xs mb-2 tracking-wide">Syllabus objectives</div>
                                      <p className="text-gray-500 text-sm italic">Syllabus mapping in progress. Check back later for specific objectives.</p>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })()}
                      </div>
                    )}
                    
                    {msg.type === 'error' && (
                      <div className="bg-red-100 border border-red-400 text-red-700 p-4 rounded-xl max-w-lg">
                        <p className="font-bold">❌ Error:</p>
                        <p>{msg.content}</p>
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </section>

        {/* Answer Submission Section */}
        <section className="container mx-auto px-4 py-12">
          <h3 className="text-3xl font-bold mb-6 text-center text-blue-600">✍️ Submit Your Answer for Feedback (Type or Upload) 📝</h3>
          <div className="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-xl">
            <textarea 
              className="w-full p-4 border rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-600" 
              rows="5" 
              placeholder="Type or upload your answer here... 💡"
            ></textarea>
            <div className="flex justify-center mb-4">
              <label className="bg-indigo-600 text-white px-6 py-3 rounded-full cursor-pointer hover:bg-indigo-700 transition font-semibold">
                Upload Answer 📤
                <input type="file" accept=".png,.jpg,.pdf,.txt" className="hidden" />
              </label>
            </div>
            <p className="text-center text-sm text-gray-600 mb-4"></p>
            <button className="w-full bg-blue-600 text-white px-8 py-4 rounded-full hover:bg-blue-700 transition font-bold">Send 🚀</button>
          </div>
        </section>
        </>
      )}

      {/* Popular Questions Section */}
      {currentSection === 'popular' && (
        <section className="bg-gray-200 py-12 min-h-screen">
          <div className="container mx-auto px-4">
            <h3 className="text-3xl font-bold mb-6 text-center gradient-text">🔥 Top 10 Popular Questions 🌟</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {popularQuestions.length > 0 ? (
                popularQuestions.map((question, idx) => (
                  <div key={idx} className="bg-white p-8 rounded-2xl shadow-xl fade-in hover:scale-105 transition">
                    <p className="font-bold text-lg mb-2">{question.content || question.original_filename}</p>
                    <p className="text-sm text-gray-600 mb-4">Asked {question.query_count || 0} times</p>
                    <button className="text-blue-600 hover:underline font-semibold">View Solution ✨</button>
                  </div>
                ))
              ) : (
                // Default popular questions when API fails
                <>
                  <div className="bg-white p-8 rounded-2xl shadow-xl fade-in hover:scale-105 transition">
                    <p className="font-bold text-lg">Solve ∫x³dx 🧮</p>
                    <button className="mt-4 text-blue-600 hover:underline font-semibold">View Solution ✨</button>
                  </div>
                  <div className="bg-white p-8 rounded-2xl shadow-xl fade-in hover:scale-105 transition">
                    <p className="font-bold text-lg">Newton's Second Law Application ⚡</p>
                    <button className="mt-4 text-blue-600 hover:underline font-semibold">View Solution ✨</button>
                  </div>
                  <div className="bg-white p-8 rounded-2xl shadow-xl fade-in hover:scale-105 transition">
                    <p className="font-bold text-lg">Quadratic Equation Roots 📊</p>
                    <button className="mt-4 text-blue-600 hover:underline font-semibold">View Solution ✨</button>
                  </div>
                </>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Student Scoreboard and Top Schools */}
      {currentSection === 'scoreboard' && (
        <section className="container mx-auto px-4 py-12 min-h-screen">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-3xl font-bold mb-6 gradient-text">🏆 Student Scoreboard 🥇</h3>
              <div className="bg-white p-8 rounded-2xl shadow-xl">
                <ul className="space-y-4">
                  <li className="flex justify-between text-lg"><span>John D. 🔥</span><span>950 pts</span></li>
                  <li className="flex justify-between text-lg"><span>Sarah K. 💪</span><span>920 pts</span></li>
                  <li className="flex justify-between text-lg"><span>Michael T. 🌟</span><span>890 pts</span></li>
                  <li className="flex justify-between text-lg"><span>Emma R. ✨</span><span>875 pts</span></li>
                  <li className="flex justify-between text-lg"><span>David L. 🚀</span><span>860 pts</span></li>
                </ul>
              </div>
            </div>
            <div>
              <h3 className="text-3xl font-bold mb-6 gradient-text">🎓 Top Schools 🏫</h3>
              <div className="bg-white p-8 rounded-2xl shadow-xl">
                <ul className="space-y-4">
                  <li className="flex justify-between text-lg"><span>St. Mary's College 📚</span><span>2500 pts</span></li>
                  <li className="flex justify-between text-lg"><span>Hillview College 🏆</span><span>2300 pts</span></li>
                  <li className="flex justify-between text-lg"><span>Presentation College ⭐</span><span>2100 pts</span></li>
                  <li className="flex justify-between text-lg"><span>Queens Royal College 👑</span><span>2050 pts</span></li>
                  <li className="flex justify-between text-lg"><span>Naparima College 🌟</span><span>2000 pts</span></li>
                </ul>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="bg-blue-600 text-white py-6">
        <div className="container mx-auto px-4 text-center">
          <p>&copy; 2025 CAPE·GPT. All rights reserved. Made with ❤️ by Gen Alpha Vibes!</p>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainApp />} />
        <Route path="/questions/:id" element={<QuestionViewer />} />
      </Routes>
    </Router>
  );
}

export default App;