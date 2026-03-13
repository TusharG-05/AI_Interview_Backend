import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, Users, FileText, Clock, CheckCircle, AlertCircle, Loader2, Settings } from 'lucide-react';

/**
 * Enhanced Loading Component
 * Professional loading states with animations
 */
const LoadingSpinner = ({ size = 'md', text = 'Loading...' }) => (
  <div className="flex flex-col items-center justify-center p-8">
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`flex flex-col items-center justify-center ${
        size === 'sm' ? 'gap-2' : size === 'lg' ? 'gap-4' : 'gap-3'
      }`}
    >
      <Loader2 className={`${size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-8 h-8' : 'w-6 h-6'} animate-spin text-blue-600`} />
      {text && (
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.3 }}
          className="text-gray-600 text-sm mt-2 text-center"
        >
          {text}
        </motion.p>
      )}
    </motion.div>
  </div>
);

/**
 * Professional Error Alert Component
 */
const ErrorAlert = ({ error, onDismiss, action }) => (
  <motion.div
    initial={{ opacity: 0, y: -20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    className="bg-red-50 border-l-4 border-red-200 p-4 rounded-lg mb-4"
  >
    <div className="flex items-start">
      <AlertCircle className="text-red-600 mr-3 flex-shrink-0 mt-0.5" size={20} />
      <div className="flex-1">
        <h3 className="text-red-800 font-semibold text-sm">Error</h3>
        <p className="text-red-700 text-sm mt-1">{error}</p>
        {action && (
          <button
            onClick={action}
            className="mt-2 bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
        )}
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="ml-4 text-red-600 hover:text-red-800 transition-colors"
        >
          ×
        </button>
      )}
    </div>
  </motion.div>
);

/**
 * Professional Success Alert Component
 */
const SuccessAlert = ({ message, onDismiss }) => (
  <motion.div
    initial={{ opacity: 0, y: -20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    className="bg-green-50 border-l-4 border-green-200 p-4 rounded-lg mb-4"
  >
    <div className="flex items-start">
      <CheckCircle className="text-green-600 mr-3 flex-shrink-0 mt-0.5" size={20} />
      <div className="flex-1">
        <h3 className="text-green-800 font-semibold text-sm">Success</h3>
        <p className="text-green-700 text-sm mt-1">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="ml-4 text-green-600 hover:text-green-800 transition-colors"
        >
          ×
        </button>
      )}
    </div>
  </motion.div>
);

/**
 * Professional Card Component
 */
const Card = ({ children, title, actions, className = '', hover = true }) => (
  <motion.div
    whileHover={hover ? { scale: 1.02 } : {}}
    className={`bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden ${className}`}
  >
    {(title || actions) && (
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
          {actions && <div className="flex gap-2">{actions}</div>}
        </div>
      </div>
    )}
    <div className="px-6 py-4">
      {children}
    </div>
  </motion.div>
);

/**
 * Professional Button Component
 */
const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  loading = false, 
  disabled = false, 
  onClick, 
  type = 'button',
  icon: Icon,
  className = ''
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500',
    success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    outline: 'border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-blue-500'
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };

  return (
    <motion.button
      whileHover={{ scale: loading ? 1 : disabled ? 1 : 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      disabled={disabled || loading}
      type={type}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className} ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      }`}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
      ) : (
        <>
          {Icon && <Icon className="w-4 h-4 mr-2" />}
          {children}
        </>
      )}
    </motion.button>
  );
};

/**
 * Professional Input Component
 */
const Input = ({ 
  label, 
  type = 'text', 
  placeholder, 
  value, 
  onChange, 
  error, 
  disabled = false,
  required = false,
  className = ''
}) => (
  <div className="mb-4">
    {label && (
      <label className={`block text-sm font-medium text-gray-700 mb-2 ${required ? 'required' : ''}`}>
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
    )}
    <motion.input
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      disabled={disabled}
      className={`w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
        error ? 'border-red-500 focus:ring-red-500' : ''
      } ${className}`}
    />
    {error && (
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-red-600 text-sm mt-1"
      >
        {error}
      </motion.p>
    )}
  </div>
);

/**
 * Professional Select Component
 */
const Select = ({ label, value, onChange, options, error, disabled = false, className = '' }) => (
  <div className="mb-4">
    {label && (
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
      </label>
    )}
    <motion.select
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      value={value}
      onChange={onChange}
      disabled={disabled}
      className={`w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
        error ? 'border-red-500 focus:ring-red-500' : ''
      } ${className}`}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </motion.select>
    {error && (
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-red-600 text-sm mt-1"
      >
        {error}
      </motion.p>
    )}
  </div>
);

/**
 * Professional Textarea Component
 */
const Textarea = ({ 
  label, 
  placeholder, 
  value, 
  onChange, 
  error, 
  disabled = false,
  rows = 4,
  className = ''
}) => (
  <div className="mb-4">
    {label && (
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
      </label>
    )}
    <motion.textarea
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      disabled={disabled}
      rows={rows}
      className={`w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
        error ? 'border-red-500 focus:ring-red-500' : ''
      } ${className}`}
    />
    {error && (
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-red-600 text-sm mt-1"
      >
        {error}
      </motion.p>
    )}
  </div>
);

/**
 * Professional File Upload Component
 */
const FileUpload = ({ label, onFileSelect, accept, error, loading = false, className = '' }) => {
  const fileInputRef = React.useRef(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      onFileSelect(file);
    }
  };

  return (
    <div className={`mb-4 ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
      )}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        whileHover={{ scale: 1.02 }}
        className={`relative border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-gray-400 transition-colors ${
          error ? 'border-red-500' : ''
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={loading}
        />
        <div className="text-center">
          {loading ? (
            <Loader2 className="w-8 h-8 mx-auto text-blue-600 animate-spin" />
          ) : (
            <div className="space-y-2">
              <FileText className="mx-auto text-gray-400" size={32} />
              <p className="text-sm text-gray-600">
                Click to upload or drag and drop
              </p>
              <p className="text-xs text-gray-500">
                {accept && `Accepts: ${accept}`}
              </p>
            </div>
          )}
        </div>
      </motion.div>
      {error && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-red-600 text-sm mt-2"
        >
          {error}
        </motion.p>
      )}
    </div>
  );
};

export {
  LoadingSpinner,
  ErrorAlert,
  SuccessAlert,
  Card,
  Button,
  Input,
  Select,
  Textarea,
  FileUpload
};
