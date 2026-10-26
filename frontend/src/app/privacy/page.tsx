"use client";

import React from "react";
import { Lock, EyeOff, Server, HardDrive, ShieldCheck } from "lucide-react";

export default function PrivacyPage() {
  const points = [
    {
      title: "Zero-Storage Guarantee",
      desc: "Uploaded images are received in an in-memory byte buffer (RAM). We do not save files to disk or write uploads to any persistent database. Memory is cleared when the request completes.",
      icon: <HardDrive className="w-5 h-5 text-primary" />,
    },
    {
      title: "No Account or Identity Tracking",
      desc: "ScamLens does not require sign-up, email registration, cookies, or personal profiles. Every scan is stateless and anonymous.",
      icon: <EyeOff className="w-5 h-5 text-primary" />,
    },
    {
      title: "Local Execution Mode Available",
      desc: "For maximum privacy, run ScamLens in Local Mode using Ollama (gemma4). Your screenshots and messages never leave your own computer or home network.",
      icon: <Server className="w-5 h-5 text-primary" />,
    },
    {
      title: "No Model Training on User Data",
      desc: "Neither your text nor uploaded images are ever used to train or fine-tune models.",
      icon: <Lock className="w-5 h-5 text-primary" />,
    },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-20 space-y-10">
      <div className="text-center space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900">
          Privacy & Zero-Retention Policy
        </h1>
        <p className="text-slate-600 max-w-xl mx-auto text-sm">
          ScamLens is built around a non-negotiable principle: your sensitive documents must never be stored.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {points.map((p, idx) => (
          <div
            key={idx}
            className="glass-panel p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3"
          >
            <div className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center">
              {p.icon}
            </div>
            <h3 className="text-base font-bold text-slate-900">{p.title}</h3>
            <p className="text-xs text-slate-600 leading-relaxed">{p.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
