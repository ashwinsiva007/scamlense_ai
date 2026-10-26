"use client";

import React, { useEffect, useState } from "react";
import { Check, Loader2, Sparkles, Network, ShieldAlert, FileText } from "lucide-react";
import { Skeleton } from "@/components/ui/Skeleton";

interface LoadingStepsProps {
  labels: {
    step1: string;
    step2: string;
    step3: string;
    step4: string;
  };
}

export function LoadingSteps({ labels }: LoadingStepsProps) {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    { label: labels.step1, icon: <FileText className="w-4 h-4" /> },
    { label: labels.step2, icon: <Network className="w-4 h-4" /> },
    { label: labels.step3, icon: <ShieldAlert className="w-4 h-4" /> },
    { label: labels.step4, icon: <Sparkles className="w-4 h-4" /> },
  ];

  useEffect(() => {
    // Smooth step advance timer while waiting for API
    const t1 = setTimeout(() => setCurrentStep(1), 500);
    const t2 = setTimeout(() => setCurrentStep(2), 1100);
    const t3 = setTimeout(() => setCurrentStep(3), 1800);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Analyzing document progress"
      className="p-6 sm:p-8 rounded-2xl glass-panel border border-slate-200/80 shadow-lg space-y-6 animate-fadeIn"
    >
      <div className="flex items-center gap-2 text-primary font-bold text-sm">
        <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
        <span>ScamLens Pipeline In Progress...</span>
      </div>

      {/* Steps List */}
      <div className="space-y-3">
        {steps.map((step, idx) => {
          const isDone = currentStep > idx;
          const isCurrent = currentStep === idx;
          const isPending = currentStep < idx;

          return (
            <div
              key={idx}
              className={`flex items-center gap-3 p-3 rounded-xl border transition-all duration-300 ${
                isCurrent
                  ? "bg-primary/5 border-primary/30 text-slate-900 shadow-sm"
                  : isDone
                  ? "bg-slate-50 border-slate-200 text-slate-700"
                  : "bg-slate-50/40 border-transparent text-slate-400"
              }`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 font-semibold text-xs transition-colors ${
                  isDone
                    ? "bg-primary text-white"
                    : isCurrent
                    ? "bg-primary/10 text-primary border border-primary/20"
                    : "bg-slate-200 text-slate-500"
                }`}
              >
                {isDone ? (
                  <Check className="w-4 h-4" />
                ) : isCurrent ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                ) : (
                  <span>{idx + 1}</span>
                )}
              </div>

              <div className="flex-1 text-xs sm:text-sm font-semibold flex items-center gap-2">
                <span className={isCurrent ? "text-primary" : ""}>{step.icon}</span>
                <span>{step.label}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Shimmering Skeletons */}
      <div className="space-y-3 pt-2 border-t border-slate-200/60">
        <Skeleton height={24} className="w-3/4" />
        <Skeleton height={16} className="w-full" />
        <Skeleton height={16} className="w-5/6" />
        <div className="grid grid-cols-2 gap-3 pt-2">
          <Skeleton height={40} className="w-full" />
          <Skeleton height={40} className="w-full" />
        </div>
      </div>
    </div>
  );
}
