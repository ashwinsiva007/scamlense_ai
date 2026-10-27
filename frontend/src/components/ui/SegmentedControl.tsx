"use client";

import React from "react";

export interface SegmentOption<T extends string> {
  value: T;
  label: string;
  icon?: React.ReactNode;
  ariaLabel?: string;
  disabled?: boolean;
  title?: string;
}

export interface SegmentedControlProps<T extends string> {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
  name?: string;
  label?: string;
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className = "",
  label,
}: SegmentedControlProps<T>) {
  return (
    <div
      role="radiogroup"
      aria-label={label || "Selection control"}
      className={`inline-flex p-1 bg-slate-100/90 border border-slate-200/80 rounded-xl gap-1 w-full ${className}`}
    >
      {options.map((option) => {
        const isSelected = value === option.value;
        const isDisabled = Boolean(option.disabled);
        return (
          <button
            key={option.value}
            role="radio"
            aria-checked={isSelected}
            aria-label={option.ariaLabel || option.label}
            title={option.title}
            type="button"
            disabled={isDisabled}
            onClick={() => {
              if (!isDisabled) {
                onChange(option.value);
              }
            }}
            className={`flex-1 min-h-[44px] py-2 px-3 text-xs sm:text-sm font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-all select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1 ${
              isDisabled
                ? "opacity-50 cursor-not-allowed text-slate-400 bg-slate-100/50 border border-transparent"
                : isSelected
                ? "bg-white text-slate-900 shadow-sm border border-slate-200/70 font-bold"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/50 border border-transparent"
            }`}
          >
            {option.icon && <span className="shrink-0">{option.icon}</span>}
            <span>{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}
