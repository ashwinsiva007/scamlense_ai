"use client";

import React, { useState, useId } from "react";
import { Info } from "lucide-react";

export interface TooltipProps {
  content: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
  position?: "top" | "bottom";
}

export function Tooltip({
  content,
  children,
  className = "",
  position = "top",
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const tooltipId = useId();

  return (
    <span
      className={`relative inline-flex items-center ${className}`}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
      onKeyDown={(e) => {
        if (e.key === "Escape") setIsVisible(false);
      }}
    >
      {children ? (
        <span
          aria-describedby={isVisible ? tooltipId : undefined}
          tabIndex={0}
          className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1 rounded cursor-help"
        >
          {children}
        </span>
      ) : (
        <button
          type="button"
          aria-describedby={isVisible ? tooltipId : undefined}
          aria-label="More information"
          className="text-slate-400 hover:text-slate-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary p-0.5 rounded cursor-help transition-colors"
        >
          <Info className="w-4 h-4" />
        </button>
      )}

      {isVisible && (
        <span
          id={tooltipId}
          role="tooltip"
          className={`absolute z-50 px-3 py-2 text-xs font-medium text-white bg-slate-900 rounded-lg shadow-xl shadow-slate-900/20 max-w-xs whitespace-normal pointer-events-none transition-all duration-150 animate-fadeIn ${
            position === "top"
              ? "bottom-full mb-2 left-1/2 -translate-x-1/2"
              : "top-full mt-2 left-1/2 -translate-x-1/2"
          }`}
        >
          {content}
          <span
            className={`absolute left-1/2 -translate-x-1/2 border-4 border-transparent ${
              position === "top"
                ? "top-full border-t-slate-900"
                : "bottom-full border-b-slate-900"
            }`}
            aria-hidden="true"
          />
        </span>
      )}
    </span>
  );
}
