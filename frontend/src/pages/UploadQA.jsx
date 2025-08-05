import { useState } from 'react';
import { motion } from 'framer-motion';
import { GlassCard, GlassButton } from '../components/GlassCard';

export default function UploadQA() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [answerFile, setAnswerFile] = useState(null);
  const [answer, setAnswer] = useState('');
  const [dragActive, setDragActive] = useState(false);

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
              
              <label className="cursor-pointer">
                <GlassButton variant="secondary" className="font-bold tracking-wide">
                  CHOOSE FILE 📂
                </GlassButton>
                <input
                  type="file"
                  accept=".png,.jpg,.jpeg,.pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
              
              {selectedFile && (
                <motion.div 
                  className="mt-6 gen-glass-card p-4 bg-lime-slush/20"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <p className="text-lime-slush font-bold text-sm">
                    📸 {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)}KB)
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
                <label className="cursor-pointer">
                  <GlassButton variant="secondary" className="font-bold tracking-wide">
                    UPLOAD ANSWER 📤
                  </GlassButton>
                  <input
                    type="file"
                    accept=".png,.jpg,.jpeg,.pdf,.txt"
                    onChange={handleAnswerFileSelect}
                    className="hidden"
                  />
                </label>
                
                {answerFile && (
                  <motion.div 
                    className="mt-4 gen-glass-card p-3 bg-bubblegum-pink/20"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3 }}
                  >
                    <p className="text-bubblegum-pink font-bold text-sm">
                      📤 {answerFile.name}
                    </p>
                  </motion.div>
                )}
              </div>

              <div className="text-center pt-4">
                <GlassButton 
                  variant="primary" 
                  className="text-xl px-12 py-4 font-bold tracking-wide"
                  disabled={!selectedFile && !answer.trim()}
                >
                  ANALYZE NOW 🚀
                </GlassButton>
              </div>
            </div>
          </GlassCard>
        </div>
      </motion.section>
    </motion.div>
  );
}