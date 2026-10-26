"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, Heart, Github, BookOpen, ExternalLink } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-20 space-y-10">
      <div className="text-center space-y-3">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900">
          About ScamLens
        </h1>
        <p className="text-slate-600 max-w-xl mx-auto text-sm">
          An open-source public interest project empowering individuals and families against modern digital deception.
        </p>
      </div>

      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-base font-bold text-slate-900">The Mission</h2>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          Digital fraud exploits information asymmetry and generational vulnerability. Fraudsters impersonate
          banks, government bodies, and courier services using fake offers and manipulated receipts. ScamLens was
          created to provide clear, transparent, and linguistically accessible explanations so anyone can protect
          themselves and their elders without compromising personal privacy.
        </p>

        <h2 className="text-base font-bold text-slate-900 pt-2">Key Principles</h2>
        <ul className="text-xs sm:text-sm text-slate-600 space-y-2 list-disc list-inside">
          <li>
            <strong className="text-slate-800">Explainable AI:</strong> The vision model reads and explains; deterministic rules and domain tools score.
          </li>
          <li>
            <strong className="text-slate-800">Quoted Evidence:</strong> Every red flag quotes verbatim words from the input.
          </li>
          <li>
            <strong className="text-slate-800">No False Comfort:</strong> The system never labels anything as &quot;safe&quot;; the baseline is &quot;no major red flags found&quot;.
          </li>
          <li>
            <strong className="text-slate-800">Zero Retention:</strong> Uploads are kept purely in RAM and never saved.
          </li>
        </ul>

        <div className="pt-4 border-t border-slate-200 flex flex-wrap gap-4">
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-white text-xs font-semibold hover:bg-primary-hover shadow-sm transition-all"
          >
            <ShieldCheck className="w-4 h-4" />
            Try ScamLens Now
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 text-slate-700 text-xs font-semibold hover:bg-slate-200 transition-all border border-slate-200"
          >
            <Github className="w-4 h-4" />
            View on GitHub
          </a>
        </div>
      </div>
    </div>
  );
}
