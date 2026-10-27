"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldAlert, Globe, Menu, X, Sparkles } from "lucide-react";
import { Language, useT } from "@/context/LanguageContext";
import { getHealth, HealthResponse } from "@/lib/api";

export const Navbar: React.FC = () => {
  const { language, setLanguage, t } = useT();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));

    const interval = setInterval(() => {
      getHealth()
        .then(setHealth)
        .catch(() => setHealth(null));
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  const navLinks = [
    { href: "/", label: t("nav.home") },
    { href: "/how-it-works", label: t("nav.howItWorks") },
    { href: "/benchmarks", label: t("nav.benchmarks") },
    { href: "/privacy", label: t("nav.privacy") },
    { href: "/about", label: t("nav.about") },
  ];

  const languages: { code: Language; label: string }[] = [
    { code: "en", label: "English" },
    { code: "ta", label: "தமிழ்" },
    { code: "hi", label: "हिन्दी" },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-200/90 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-18">
          {/* Logo & Brand */}
          <Link
            href="/"
            className="flex items-center gap-2.5 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-xl p-1"
          >
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-white shadow-md shadow-primary/20 group-hover:scale-105 transition-transform">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xl font-extrabold tracking-tight text-slate-900 flex items-center gap-1">
                Scam<span className="text-primary">Lens</span>
              </span>
              <span className="hidden sm:block text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
                {t("nav.tagline")}
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav
            role="navigation"
            aria-label="Main Navigation"
            className="hidden md:flex items-center space-x-1 lg:space-x-2"
          >
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`min-h-[44px] px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                    isActive
                      ? "text-primary bg-primary/10 font-bold"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Connection Status Badge */}
          <div className="hidden sm:flex items-center">
            {health?.mode === "cloud" && health?.key_configured ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Cloud connected
              </span>
            ) : health?.mode === "cloud" && !health?.key_configured ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                Cloud: key missing
              </span>
            ) : health?.mode === "local" ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-sky-50 text-sky-700 border border-sky-200">
                <span className="w-2 h-2 rounded-full bg-sky-500"></span>
                Local mode
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                Demo mode
              </span>
            )}
          </div>

          {/* Language Switcher & Controls */}
          <div className="flex items-center gap-2">
            <div
              role="group"
              aria-label="Language selector"
              className="flex items-center bg-slate-100/90 rounded-xl p-1 border border-slate-200"
            >
              <Globe className="w-4 h-4 text-slate-400 ml-2 mr-1 hidden sm:block" />
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => setLanguage(lang.code)}
                  className={`min-h-[38px] px-3 py-1.5 text-xs rounded-lg font-semibold transition-all select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                    language === lang.code
                      ? "bg-white text-slate-900 shadow-sm border border-slate-200/60 font-bold"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                  aria-label={`Switch language to ${lang.label}`}
                >
                  {lang.label}
                </button>
              ))}
            </div>

            {/* Mobile menu toggle button */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden min-h-[44px] min-w-[44px] p-2.5 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 flex items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              aria-label="Toggle Navigation Menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile navigation drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white/95 backdrop-blur-md px-4 pt-3 pb-5 space-y-1.5 animate-fadeIn">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`block min-h-[44px] px-4 py-3 rounded-xl text-sm font-semibold flex items-center ${
                  isActive
                    ? "text-primary bg-primary/10 font-bold"
                    : "text-slate-700 hover:bg-slate-100"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      )}
    </header>
  );
};
