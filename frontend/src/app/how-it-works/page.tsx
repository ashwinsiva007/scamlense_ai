"use client";

import React from "react";
import { Cpu, ShieldAlert, CheckCircle, Network, ArrowRight } from "lucide-react";
import { useT } from "@/context/LanguageContext";

export default function HowItWorksPage() {
  const { t } = useT();

  const steps = [
    {
      step: "01",
      title: "In-Memory Ingestion",
      desc: "Screenshots and text are loaded strictly into RAM. No files are written to disk or stored in any database.",
      icon: <Cpu className="w-6 h-6 text-primary" />,
    },
    {
      step: "02",
      title: "Multimodal Perception (Gemma 4)",
      desc: "The vision model extracts verbatim text, phone numbers, UPI VPAs, and claimed brands. It does NOT assign risk scores.",
      icon: <Network className="w-6 h-6 text-primary" />,
    },
    {
      step: "03",
      title: "Deterministic Rule Scoring",
      desc: "Open-source YAML rule packs score the extracted entities. Every red flag must quote exact text present in the input.",
      icon: <ShieldAlert className="w-6 h-6 text-warning" />,
    },
    {
      step: "04",
      title: "Multilingual Explanation & Alert",
      desc: "The explainer synthesizes findings into plain English, Tamil, or Hindi, producing an actionable Family Alert card.",
      icon: <CheckCircle className="w-6 h-6 text-emerald-600" />,
    },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-20 space-y-12">
      <div className="text-center space-y-3">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900">
          How ScamLens Works
        </h1>
        <p className="text-slate-600 max-w-2xl mx-auto text-sm sm:text-base">
          A fundamental separation between AI perception (reading content) and transparent rules (deciding risk).
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {steps.map((s) => (
          <div
            key={s.step}
            className="glass-panel p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center">
                {s.icon}
              </div>
              <span className="text-2xl font-black text-slate-300 font-mono">
                {s.step}
              </span>
            </div>
            <h3 className="text-base font-bold text-slate-900">{s.title}</h3>
            <p className="text-xs text-slate-600 leading-relaxed">{s.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
