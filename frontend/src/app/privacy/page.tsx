"use client";

import React from "react";
import {
  Lock,
  EyeOff,
  Server,
  HardDrive,
  ShieldCheck,
  Cpu,
  Cloud,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

export default function PrivacyPage() {
  const policies = [
    {
      title: "Zero-Storage Guarantee",
      badge: "In-Memory RAM Only",
      desc: "Uploaded images and pasted texts are processed exclusively in volatile memory (RAM). ScamLens has no database, no file server, and no cloud object buckets. All buffer bytes are released the moment the HTTP response finishes.",
      icon: <HardDrive className="w-5 h-5 text-primary" />,
    },
    {
      title: "No Account or Identity Tracking",
      badge: "Stateless & Anonymous",
      desc: "ScamLens requires no login, no email address, and no personal profile. We store no session cookies and build no behavioral user graph.",
      icon: <EyeOff className="w-5 h-5 text-primary" />,
    },
    {
      title: "No Model Training on Uploads",
      badge: "Zero-Retention APIs",
      desc: "Neither your screenshots nor your extracted messages are used to train, tune, or evaluate AI models under any circumstances.",
      icon: <Lock className="w-5 h-5 text-primary" />,
    },
    {
      title: "Airgapped Local Mode Available",
      badge: "100% Private Offline",
      desc: "For highly sensitive financial files, switch to 'Private, local' mode powered by a local Ollama server. Not a single byte leaves your computer.",
      icon: <Server className="w-5 h-5 text-primary" />,
    },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-16 space-y-12">
      {/* Page Header */}
      <div className="text-center space-y-3 max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Stateless Privacy Guarantee</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Privacy Policy &amp; Architecture
        </h1>
        <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-medium">
          A transparent explanation of how ScamLens handles your screenshots, what is sent where, and how you retain complete control.
        </p>
      </div>

      {/* Cloud vs Local Mode Comparison Table */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-200 space-y-6 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">
          Operating Modes: Cloud vs. Local
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Cloud Mode */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cloud className="w-5 h-5 text-info" />
                <h3 className="text-base font-bold text-slate-900">Cloud, Verified</h3>
              </div>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-info-light text-info-dark">
                Fast &amp; Connected
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed font-medium">
              Uses Google Gemini cloud inference under strict Zero Data Retention agreements.
            </p>

            <div className="space-y-1.5 pt-2 border-t border-slate-100 text-xs text-slate-700">
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <span>Processes in ~1 second with state-of-the-art vision models.</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <span>Queries Google Safe Browsing and URLhaus to catch active phishing.</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <span>Zero persistence: neither Google nor ScamLens stores your image.</span>
              </div>
            </div>
          </div>

          {/* Local Mode */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Server className="w-5 h-5 text-primary" />
                <h3 className="text-base font-bold text-slate-900">Private, Local</h3>
              </div>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-primary-light text-primary">
                100% Offline
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed font-medium">
              Routes model calls directly to a local Ollama instance running on your machine.
            </p>

            <div className="space-y-1.5 pt-2 border-t border-slate-100 text-xs text-slate-700">
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <span>Zero external network transmissions for model reasoning.</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <span>Ideal for sensitive financial statements and private letters.</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <span>Open-source rule packs run locally on your CPU/GPU.</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Advisory to blur personal data */}
      <div className="p-5 sm:p-6 rounded-2xl bg-amber-50/80 border border-warning/30 flex items-start gap-4">
        <AlertCircle className="w-6 h-6 text-warning shrink-0 mt-0.5" />
        <div className="space-y-1 text-xs sm:text-sm text-slate-800">
          <h3 className="font-bold text-warning-dark">
            Proactive Best Practice: Blur Sensitive Personal Identifiers
          </h3>
          <p className="leading-relaxed">
            While ScamLens never retains uploaded media, we strongly encourage users to redact or blur their full bank account numbers, Aadhaar numbers, and physical residential addresses using their phone or PC markup tool before uploading screenshots to Cloud Mode.
          </p>
        </div>
      </div>

      {/* Privacy Guarantees Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {policies.map((p, idx) => (
          <div
            key={idx}
            className="glass-panel p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center">
                {p.icon}
              </div>
              <span className="text-[11px] font-semibold text-slate-500 font-mono">
                {p.badge}
              </span>
            </div>
            <h3 className="text-base font-bold text-slate-900">{p.title}</h3>
            <p className="text-xs text-slate-600 leading-relaxed font-medium">{p.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
