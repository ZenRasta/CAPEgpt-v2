import { useState, forwardRef } from 'react';

const DropZone = forwardRef(function DropZone({ onDrop, onChange, disabled = false, className = '', children }, ref) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    onDrop && onDrop(e);
  };

  const handleClick = () => {
    if (!disabled) {
      ref?.current?.click();
    }
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg text-center transition-colors ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${isDragging ? 'border-purple-500 bg-purple-50' : 'border-gray-300 hover:border-purple-500'} ${className}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input ref={ref} type="file" className="hidden" onChange={onChange} />
      {children}
    </div>
  );
});

export default DropZone;

