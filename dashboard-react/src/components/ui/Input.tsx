import React, { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', label, error, fullWidth = false, ...props }, ref) => {
    return (
      <div className={`flex flex-col gap-1.5 ${fullWidth ? 'w-full' : ''}`}>
        {label && (
          <label className="text-sm font-medium text-slate-700">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`
            px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm shadow-sm
            placeholder-slate-400
            focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500
            disabled:bg-slate-50 disabled:text-slate-500
            transition-colors
            ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
            ${className}
          `}
          {...props}
        />
        {error && (
          <span className="text-xs text-red-500 mt-0.5">{error}</span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
