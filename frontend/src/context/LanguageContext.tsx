"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import en from "@/i18n/en.json";
import ta from "@/i18n/ta.json";
import hi from "@/i18n/hi.json";

export type Language = "en" | "ta" | "hi";

type Translations = typeof en;

const translations: Record<Language, Translations> = {
  en,
  ta,
  hi,
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
      const saved = localStorage.getItem("scamlens_lang") as Language;
      if (saved && (saved === "en" || saved === "ta" || saved === "hi")) {
        setLanguageState(saved);
      }
    } catch {
      // localStorage may be unavailable in some sandboxes
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    try {
      localStorage.setItem("scamlens_lang", lang);
    } catch {
      // ignore
    }
  };

  const t = (path: string): string => {
    const keys = path.split(".");
    let current: any = translations[language] || translations.en;
    for (const key of keys) {
      if (current && typeof current === "object" && key in current) {
        current = current[key];
      } else {
        // fallback to english
        let fallback: any = translations.en;
        for (const fbKey of keys) {
          if (fallback && typeof fallback === "object" && fbKey in fallback) {
            fallback = fallback[fbKey];
          } else {
            return path;
          }
        }
        return typeof fallback === "string" ? fallback : path;
      }
    }
    return typeof current === "string" ? current : path;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useT = () => useContext(LanguageContext);
