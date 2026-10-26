"use client";

import React, { createContext, useContext, useEffect, useState, useMemo } from "react";
import en from "@/i18n/en.json";
import ta from "@/i18n/ta.json";
import hi from "@/i18n/hi.json";

export type Language = "en" | "ta" | "hi";

type TranslationRecord = Record<string, unknown>;

const translations: Record<Language, TranslationRecord> = {
  en: en as unknown as TranslationRecord,
  ta: ta as unknown as TranslationRecord,
  hi: hi as unknown as TranslationRecord,
};

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (path: string) => string;
}

const LanguageContext = createContext<LanguageContextType>({
  language: "en",
  setLanguage: () => {},
  t: (path: string) => path,
});

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>("en");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("scamlens_lang") as Language | null;
      if (saved && (saved === "en" || saved === "ta" || saved === "hi")) {
        setLanguageState(saved);
        document.documentElement.lang = saved;
        document.documentElement.setAttribute("data-lang", saved);
      } else {
        document.documentElement.lang = "en";
        document.documentElement.setAttribute("data-lang", "en");
      }
    } catch {
      // In case localStorage is blocked in sandbox
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    try {
      localStorage.setItem("scamlens_lang", lang);
      document.documentElement.lang = lang;
      document.documentElement.setAttribute("data-lang", lang);
    } catch {
      // ignore
    }
  };

  const t = useMemo(() => {
    return (path: string): string => {
      const keys = path.split(".");
      let current: unknown = translations[language] || translations.en;

      for (const key of keys) {
        if (current && typeof current === "object" && key in (current as Record<string, unknown>)) {
          current = (current as Record<string, unknown>)[key];
        } else {
          // Fallback to English
          let fallback: unknown = translations.en;
          for (const fbKey of keys) {
            if (fallback && typeof fallback === "object" && fbKey in (fallback as Record<string, unknown>)) {
              fallback = (fallback as Record<string, unknown>)[fbKey];
            } else {
              return path;
            }
          }
          return typeof fallback === "string" ? fallback : path;
        }
      }

      return typeof current === "string" ? current : path;
    };
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useT = () => useContext(LanguageContext);
