"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldAlert, Globe, Menu, X } from "lucide-react";
import { Language, useT } from "@/context/LanguageContext";

export const Navbar: React.FC = () => {
  const { language, setLanguage, t } = useT();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { href: "/", label: t("nav.home") },
    { href: "/how-it-works", label: t("nav.howItWorks") },
    { href: "/benchmarks", label: t("nav.benchmarks") },
    { href: "/privacy", label: t("nav.privacy") },
    { href: "/about", label: t("nav.about") },
  ];

  const languages: { code: Language; label: string }[] = [
    { code: "en", label: "EN" },
    { code: "ta", label: "தமிழ்" },
    { code: "hi", label: "हिन्दी" },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-white shadow-md shadow-primary/20 group-hover:scale-105 transition-transform">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-1.5">
                Scam<span className="text-primary">Lens</span>
              </span>
              <span className="hidden sm:block text-[10px] text-slate-500 font-medium uppercase tracking-wider">
                {t("nav.tagline")}
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-1 lg:space-x-2">
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "text-primary bg-primary/10 font-semibold"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Language Switcher & Controls */}
          <div className="flex items-center gap-2">
            <div className="flex items-center bg-slate-100 rounded-lg p-1 border border-slate-200">
              <Globe className="w-4 h-4 text-slate-500 ml-1.5 mr-1 hidden sm:block" />
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => setLanguage(lang.code)}
                  className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
                    language === lang.code
                      ? "bg-white text-primary shadow-sm font-semibold"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                  title={`Switch language to ${lang.label}`}
                >
                  {lang.label}
                </button>
              ))}
            </div>

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile navigation drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white/95 backdrop-blur-md px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-3 py-2 rounded-lg text-sm font-medium ${
                  isActive
                    ? "text-primary bg-primary/10 font-semibold"
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
