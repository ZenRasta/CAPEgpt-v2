import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { GlassCard, GlassButton } from '../components/GlassCard';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function UploadQA() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [answerFile, setAnswerFile] = useState(null);
  const [answer, setAnswer] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [processingStage, setProcessingStage] = useState('');
  const [questionId, setQuestionId] = useState(null);
  const [error, setError] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const navigate = useNavigate();
  
  const fileInputRef = useRef(null);
  const answerFileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleAnswerFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setAnswerFile(e.target.files[0]);
    }
  };

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
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const uploadAndProcessQuestion = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setProcessing(true);
    setError(null);
    setProcessingStage('Uploading file...');

    try {
      // Step 1: Upload question file
      const formData = new FormData();
      formData.append('file', selectedFile);

      const uploadResponse = await fetch(`${API_BASE_URL}/questions/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.status}`);
      }

      const uploadResult = await uploadResponse.json();
      setQuestionId(uploadResult.id);
      setUploadSuccess(true);
      setProcessingStage('Processing with MathPix and Google Vision...');

      // Step 2: Poll for processing completion
      await pollProcessingStatus(uploadResult.id);

      // Step 3: Get AI analysis
      await getAIAnalysis(uploadResult.id);

    } catch (err) {
      console.error('Upload/processing error:', err);
      setError(err.message || 'Failed to process question');
      setProcessing(false);
    }
  };

  const pollProcessingStatus = async (id) => {
    let attempts = 0;
    const maxAttempts = 60; // 60 attempts = ~2 minutes with backoff
    
    return new Promise((resolve, reject) => {
      const checkStatus = async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/questions/${id}`);
          if (!response.ok) {
            throw new Error('Failed to check processing status');
          }
          
          const question = await response.json();
          
          if (question.processing_status === 'completed') {
            setProcessingStage('Processing completed! Getting AI analysis...');
            resolve(question);
          } else if (question.processing_status === 'failed') {
            const errorMsg = question.processing_error || 'Unknown processing error occurred';
            const userFriendlyMsg = errorMsg.includes('OCR services are not configured') 
              ? 'Image processing is currently unavailable. Please type your question in the text area below instead.'
              : `Processing failed: ${errorMsg}`;
            reject(new Error(userFriendlyMsg));
          } else {
            attempts++;
            if (attempts >= maxAttempts) {
              reject(new Error('Processing is taking longer than usual—please try again in a minute.'));
            } else {
              // Backoff: start at 1s, increase gradually to max 4s
              const delay = Math.min(1000 + attempts * 250, 4000);
              setProcessingStage(`Processing... (${attempts}/${maxAttempts})`);
              setTimeout(checkStatus, delay);
            }
          }
        } catch (err) {
          reject(err);
        }
      };
      
      checkStatus();
    });
  };

  const getAIAnalysis = async (id) => {
    try {
      setProcessingStage('Getting AI analysis...');
      
      // First get the processed question
      const questionResponse = await fetch(`${API_BASE_URL}/questions/${id}`);
      if (!questionResponse.ok) {
        throw new Error('Failed to get question details');
      }
      
      const questionData = await questionResponse.json();
      
      if (!questionData.mathpix_markdown && !questionData.ocr_fallback_text) {
        const errorDetail = questionData.processing_error ? ` (${questionData.processing_error})` : '';
        throw new Error(`No text content available for analysis${errorDetail}`);
      }
      
      // Use the processed text for AI analysis
      const queryText = questionData.mathpix_markdown || questionData.ocr_fallback_text;
      const subject = questionData.subject || 'Pure Mathematics';
      
      const analysisResponse = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: queryText,
          subject: subject,
        }),
      });

      if (!analysisResponse.ok) {
        throw new Error(`Analysis failed: ${analysisResponse.status}`);
      }

      const analysisResult = await analysisResponse.json();
      setAiAnalysis(analysisResult);
      setProcessingStage('Complete! 🎉');
      setProcessing(false);

    } catch (err) {
      console.error('AI analysis error:', err);
      setError(err.message || 'Failed to get AI analysis');
      setProcessing(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.3
      }
    }
  };

  const sectionVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.6,
        ease: "easeOut"
      }
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="py-8"
    >
      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type="file"
        name="file"
        accept=".png,.jpg,.jpeg,.pdf"
        onChange={handleFileSelect}
        className="sr-only"
        aria-label="Upload question file"
      />
      <input
        ref={answerFileInputRef}
        type="file"
        name="answerFile"
        accept=".png,.jpg,.jpeg,.pdf,.txt"
        onChange={handleAnswerFileSelect}
        className="sr-only"
        aria-label="Upload answer file"
      />
      {/* Hero Section */}
      <motion.section 
        className="container mx-auto px-4 mb-16"
        variants={sectionVariants}
      >
        <div className="text-center mb-12">
          <motion.h1 
            className="text-5xl md:text-6xl font-extrabold mb-6 gen-gradient-text tracking-tight"
            animate={{ 
              textShadow: [
                "0 0 20px rgba(35, 240, 255, 0.5)",
                "0 0 40px rgba(255, 93, 162, 0.5)",
                "0 0 20px rgba(35, 240, 255, 0.5)"
              ]
            }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          >
            DROP YOUR QUESTION 📸
          </motion.h1>
          <p className="text-xl text-white/90 font-medium tracking-wide max-w-2xl mx-auto">
            SNAP A PAST-PAPER QUESTION AND GET INSTANT AI ANALYSIS
          </p>
        </div>
      </motion.section>

      {/* File Upload Section */}
      <motion.section 
        className="container mx-auto px-4 mb-16"
        variants={sectionVariants}
      >
        <div className="max-w-2xl mx-auto">
          <GlassCard className="p-8">
            <h2 className="text-2xl font-bold mb-6 text-center gen-gradient-text tracking-wide">
              UPLOAD QUESTION IMAGE
            </h2>
            
            {/* Drag & Drop Area */}
            <div 
              className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all mb-6 ${
                dragActive 
                  ? 'border-electric-cyan bg-electric-cyan/10' 
                  : 'border-white/30 hover:border-lime-slush/50'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <motion.div 
                className="w-20 h-20 bg-gradient-to-r from-lime-slush to-electric-cyan rounded-full flex items-center justify-center mx-auto mb-6"
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              >
                <span className="text-4xl">📸</span>
              </motion.div>
              
              <h3 className="text-xl font-bold text-white mb-4 tracking-wide">
                DRAG & DROP OR CLICK TO UPLOAD
              </h3>
              <p className="text-white/80 mb-6 font-medium">
                PNG, JPG, PDF • Max file size: 10MB
              </p>
              
              <GlassButton 
                variant="secondary" 
                className="w-full flex items-center justify-center gap-3 font-bold tracking-wide"
                onClick={() => fileInputRef.current?.click()}
                disabled={processing}
              >
                📂 CHOOSE FILE
              </GlassButton>
              
              {selectedFile && (
                <motion.div 
                  className="mt-6 gen-glass-card p-4 bg-lime-slush/20"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <p className="text-lime-slush font-bold text-sm truncate">
                    📸 {selectedFile.name.length > 30 ? `${selectedFile.name.substring(0, 30)}...` : selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)}KB)
                  </p>
                </motion.div>
              )}
            </div>
          </GlassCard>
        </div>
      </motion.section>

      {/* Answer Submission Section */}
      <motion.section 
        className="container mx-auto px-4 mb-16"
        variants={sectionVariants}
      >
        <div className="max-w-2xl mx-auto">
          <GlassCard className="p-8">
            <h2 className="text-2xl font-bold mb-6 text-center gen-gradient-text tracking-wide">
              ✍️ SUBMIT YOUR ANSWER FOR FEEDBACK 📝
            </h2>
            
            <div className="space-y-6">
              <div>
                <label className="block text-white font-semibold mb-3 tracking-wide">
                  TYPE YOUR ANSWER 💭
                </label>
                <textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  className="w-full p-4 bg-white/10 border border-white/20 rounded-2xl 
                           text-white placeholder-white/60 focus:outline-none focus:border-electric-cyan 
                           focus:ring-2 focus:ring-electric-cyan/50 transition-all backdrop-blur-sm"
                  rows="6"
                  placeholder="Type or upload your answer here... 💡"
                />
              </div>

              <div className="text-center">
                <p className="text-white/80 mb-4 font-medium">OR</p>
                <GlassButton 
                  variant="secondary" 
                  className="font-bold tracking-wide"
                  onClick={() => answerFileInputRef.current?.click()}
                  disabled={processing}
                >
                  📤 UPLOAD ANSWER
                </GlassButton>
                
                {answerFile && (
                  <motion.div 
                    className="mt-4 gen-glass-card p-3 bg-bubblegum-pink/20"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3 }}
                  >
                    <p className="text-bubblegum-pink font-bold text-sm truncate">
                      📤 {answerFile.name.length > 30 ? `${answerFile.name.substring(0, 30)}...` : answerFile.name}
                    </p>
                  </motion.div>
                )}
              </div>

              <div className="text-center pt-4">
                <GlassButton 
                  variant="primary" 
                  className="text-xl px-12 py-4 font-bold tracking-wide"
                  onClick={uploadAndProcessQuestion}
                  disabled={processing || (!selectedFile && !answer.trim())}
                >
                  {processing ? processingStage || 'PROCESSING...' : 'ANALYZE NOW 🚀'}
                </GlassButton>
              </div>
            </div>
          </GlassCard>
        </div>
      </motion.section>

      {/* Error Display */}
      {error && (
        <motion.section 
          className="container mx-auto px-4 mb-16"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <div className="max-w-2xl mx-auto">
            <GlassCard className="p-6 bg-red-500/20 border border-red-400/30">
              <div className="text-center">
                <h3 className="text-2xl font-bold text-red-200 mb-4">❌ Error</h3>
                <p className="text-red-100 font-medium">{error}</p>
                <button 
                  onClick={() => setError(null)}
                  className="mt-4 px-6 py-2 bg-red-400/20 text-red-100 rounded-lg font-bold hover:bg-red-400/30 transition-all"
                >
                  Dismiss
                </button>
              </div>
            </GlassCard>
          </div>
        </motion.section>
      )}

      {/* Processing Status */}
      {processing && (
        <motion.section 
          className="container mx-auto px-4 mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="max-w-2xl mx-auto">
            <GlassCard className="p-8">
              <div className="text-center">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  className="w-16 h-16 border-4 border-electric-cyan border-t-transparent rounded-full mx-auto mb-6"
                />
                <h3 className="text-2xl font-bold gen-gradient-text mb-4">PROCESSING...</h3>
                <p className="text-white/80 text-lg font-medium">{processingStage}</p>
              </div>
            </GlassCard>
          </div>
        </motion.section>
      )}

      {/* AI Analysis Results */}
      {aiAnalysis && (
        <motion.section 
          className="container mx-auto px-4 mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="max-w-4xl mx-auto">
            <GlassCard className="p-8">
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold gen-gradient-text mb-4">🤖 AI ANALYSIS</h2>
                <p className="text-white/80 text-lg">Here's your comprehensive solution!</p>
              </div>
              
              <div className="prose prose-lg max-w-none text-white/90">
                <div className="bg-white/10 p-6 rounded-xl border border-white/20 mb-6">
                  <ReactMarkdown
                    remarkPlugins={[remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    className="text-white/90"
                  >
                    {aiAnalysis.answer}
                  </ReactMarkdown>
                </div>
                
                {/* Analysis Metadata */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
                  {aiAnalysis.topics && aiAnalysis.topics.length > 0 && (
                    <div className="bg-lime-slush/20 p-4 rounded-xl border border-lime-slush/30">
                      <h4 className="font-bold text-lime-slush mb-2">📚 Topics Covered</h4>
                      <div className="flex flex-wrap gap-2">
                        {aiAnalysis.topics.map((topic, idx) => (
                          <span key={idx} className="px-2 py-1 bg-lime-slush/30 text-lime-slush rounded text-sm">
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {aiAnalysis.years && aiAnalysis.years.length > 0 && (
                    <div className="bg-electric-cyan/20 p-4 rounded-xl border border-electric-cyan/30">
                      <h4 className="font-bold text-electric-cyan mb-2">📅 Related Years</h4>
                      <div className="flex flex-wrap gap-2">
                        {aiAnalysis.years.slice(0, 5).map((year, idx) => (
                          <span key={idx} className="px-2 py-1 bg-electric-cyan/30 text-electric-cyan rounded text-sm">
                            {year}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {aiAnalysis.confidence_score && (
                    <div className="bg-bubblegum-pink/20 p-4 rounded-xl border border-bubblegum-pink/30">
                      <h4 className="font-bold text-bubblegum-pink mb-2">🎯 Confidence</h4>
                      <div className="flex items-center gap-2">
                        <div className="bg-bubblegum-pink/30 h-3 rounded-full flex-1 overflow-hidden">
                          <div 
                            className="bg-bubblegum-pink h-full rounded-full transition-all duration-500"
                            style={{ width: `${Math.round(aiAnalysis.confidence_score * 100)}%` }}
                          />
                        </div>
                        <span className="text-bubblegum-pink font-bold text-sm">
                          {Math.round(aiAnalysis.confidence_score * 100)}%
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-4 justify-center mt-8">
                  {questionId && (
                    <GlassButton 
                      variant="secondary"
                      onClick={() => navigate(`/question/${questionId}`)}
                      className="font-bold"
                    >
                      📖 View Processed Question
                    </GlassButton>
                  )}
                  <GlassButton 
                    variant="primary"
                    onClick={() => window.location.reload()}
                    className="font-bold"
                  >
                    🔄 Analyze Another Question
                  </GlassButton>
                </div>
              </div>
            </GlassCard>
          </div>
        </motion.section>
      )}
    </motion.div>
  );
}