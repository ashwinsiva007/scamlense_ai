"use client";

import React from "react";

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onChange, className = "" }: TabsProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>, currentIndex: number) => {
    if (e.key === "ArrowRight") {
      const nextIndex = (currentIndex + 1) % tabs.length;
      onChange(tabs[nextIndex].id);
    } else if (e.key === "ArrowLeft") {
      const prevIndex = (currentIndex - 1 + tabs.length) % tabs.length;
      onChange(tabs[prevIndex].id);
    }
  };

  return (
    <div
      role="tablist"
      aria-label="Input mode selector"
      className={`flex border-b border-slate-200/90 gap-1 sm:gap-2 ${className}`}
    >
      {tabs.map((tab, idx) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            role="tab"
            id={`tab-${tab.id}`}
            aria-controls={`panel-${tab.id}`}
            aria-selected={isActive}
            tabIndex={isActive ? 0 : -1}
            onClick={() => onChange(tab.id)}
            onKeyDown={(e) => handleKeyDown(e, idx)}
            className={`min-h-[44px] pb-3 px-3 sm:px-5 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:rounded-t-lg ${
              isActive
                ? "border-primary text-primary"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            {tab.icon && <span className="shrink-0">{tab.icon}</span>}
            <span>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
