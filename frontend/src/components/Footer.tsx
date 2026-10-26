"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, PhoneCall, ExternalLink, AlertTriangle } from "lucide-react";
import { useT } from "@/context/LanguageContext";

export const Footer: React.FC = () => {
  const { t } = useT();

  return (
    <footer className="mt-auto border-t border-slate-200 bg-white/60 backdrop-blur-sm text-slate-600 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          {/* Brand & Purpose */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center text-white">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <span className="font-bold text-slate-900 text-base">ScamLens</span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Open-source fraud intelligence separating perception (AI) from judgment (rules & verifiers).
              Zero-storage privacy guarantee for every scan.
            </p>
          </div>

          {/* Official Indian Reporting Channels */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <PhoneCall className="w-3.5 h-3.5 text-primary" />
              Report Cyber Fraud (India)
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <span className="text-slate-700 font-medium">Helpline:</span>{" "}
                <a
                  href="tel:1930"
                  className="font-bold text-danger hover:underline inline-flex items-center gap-1"
                >
                  Dial 1930 <span className="text-[10px] font-normal text-slate-500">(Immediate Financial Freeze)</span>
                </a>
              </li>
              <li>
                <a
                  href="https://cybercrime.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline inline-flex items-center gap-1"
                >
                  National Cybercrime Portal (cybercrime.gov.in)
                  <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
              </li>
              <li>
                <a
                  href="https://sancharsaathi.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline inline-flex items-center gap-1"
                >
                  DoT Sanchar Saathi (Chakshu & CEIR)
                  <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
              </li>
            </ul>
          </div>

          {/* Quick Links & Legal */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900">
              {t("footer.linksHeader")}
            </h4>
            <ul className="space-y-1.5 text-xs">
              <li>
                <Link href="/how-it-works" className="hover:text-primary transition-colors">
                  {t("nav.howItWorks")}
                </Link>
              </li>
              <li>
                <Link href="/benchmarks" className="hover:text-primary transition-colors">
                  {t("nav.benchmarks")}
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="hover:text-primary transition-colors">
                  {t("nav.privacy")}
                </Link>
              </li>
              <li>
                <Link href="/about" className="hover:text-primary transition-colors">
                  {t("nav.about")}
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Mandatory Disclaimer Box */}
        <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 mb-6">
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-warning shrink-0 mt-0.5" />
            <p className="text-xs text-slate-600 leading-relaxed">
              {t("footer.disclaimer")}
            </p>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between pt-4 border-t border-slate-200 text-xs text-slate-500 gap-2">
          <p>© 2026 ScamLens Contributors. {t("footer.rights")}</p>
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              API Status: Ready
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
