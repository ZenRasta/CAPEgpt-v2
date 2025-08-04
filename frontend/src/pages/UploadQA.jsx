import { useState } from 'react';

function Hero() {
  return (
    <section className="relative bg-hero-gradient text-white">
      <div className="container min-h-[240px] lg:min-h-[300px] flex flex-col items-center justify-center text-center">
        <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tightish">
          Drop Your Question 📸
        </h1>
        <p className="mt-3 text-lg lg:text-xl opacity-95 max-w-2xl">
          Snap a CAPE question and get instant AI analysis
        </p>
      </div>
    </section>
  );
}

function Section({ title, children }) {
  return (
    <section className="bg-brand-bg">
      <div className="container py-12 lg:py-16">
        {title && <h2 className="text-2xl lg:text-3xl font-extrabold text-brand-blue text-center mb-6">{title}</h2>}
        {children}
      </div>
    </section>
  );
}

function Card({ children }) {
  return (
    <div className="bg-white rounded-3xl p-6 lg:p-8 shadow-card hover:-translate-y-0.5 hover:shadow-xl transition">
      {children}
    </div>
  );
}

export default function UploadQA() {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [subject, setSubject] = useState('Pure Mathematics');

  const subjects = [
    'Pure Mathematics',
    'Applied Mathematics', 
    'Physics',
    'Chemistry'
  ];

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

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  return (
    <>
      <Hero />
      <Section>
        <div className="max-w-2xl mx-auto">
          <Card>
          {/* File Upload Area */}
          <div 
            className={`border-2 border-dashed rounded-2xl p-8 text-center transition-colors mb-6 ${
              dragActive ? 'border-brand-blue bg-blue-50/80' : 'border-gray-300'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="w-16 h-16 bg-hero-gradient rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">📸</span>
            </div>
            <h4 className="text-lg font-semibold text-gray-900 mb-2">
              Upload Your CAPE Question
            </h4>
            <p className="text-gray-600 mb-4">
              Drag and drop an image here, or click to browse
            </p>
            
            <label className="inline-flex items-center justify-center rounded-full bg-brand-blue text-white
                             font-semibold px-6 py-3 shadow-pill hover:shadow-lg hover:opacity-95 transition cursor-pointer">
              Choose File 📂
              <input
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
              />
            </label>
            
            {selectedFile && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-700 text-sm font-medium">
                  📸 {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)}KB)
                </p>
              </div>
            )}
          </div>

          {/* Subject Selection */}
          <div className="mb-6">
            <label className="block text-lg font-semibold text-gray-900 mb-3">
              Choose Your Subject 🎓
            </label>
            <select 
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full p-4 rounded-2xl border-2 border-gray-200 focus:border-brand-blue focus:outline-none font-medium"
            >
              {subjects.map(subj => (
                <option key={subj} value={subj}>
                  {subj === 'Pure Mathematics' ? 'Pure Math 📊' : 
                   subj === 'Applied Mathematics' ? 'Applied Math 📈' : 
                   subj === 'Physics' ? 'Physics ⚡' :
                   'Chemistry 🧪'}
                </option>
              ))}
            </select>
          </div>

          {/* Text Input */}
          <div className="mb-6">
            <label className="block text-lg font-semibold text-gray-900 mb-3">
              Or Type Your Question 💭
            </label>
            <textarea
              placeholder="Paste your question text here..."
              rows="4"
              className="w-full p-4 border-2 border-gray-200 rounded-2xl focus:border-brand-blue focus:outline-none resize-none"
            />
          </div>

          {/* Submit Button */}
          <div className="text-center">
            <button className="inline-flex items-center justify-center rounded-full bg-brand-blue text-white
                               font-semibold px-8 py-3 shadow-pill hover:shadow-lg hover:opacity-95 transition">
              Analyze Question 🚀
            </button>
          </div>

          {/* Helper Text */}
          <p className="text-center text-sm text-gray-500 mt-4">
            Supported formats: PNG, JPG, PDF • Max file size: 10MB
          </p>
        </Card>
        </div>
      </Section>
    </>
  );
}