"use client";

import React, { createContext, useContext, useEffect, useState, useMemo, useCallback } from "react";
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
  t: (path: string, params?: Record<string, string | number>) => string;
}

const LanguageContext = createContext<LanguageContextType>({
  language: "en",
  setLanguage: () => {},
  t: (path: string) => path,
});

function getClientSavedLanguage(): Language | null {
  if (typeof window === "undefined") return null;
  try {
    // 1. Try cookie
    const match = document.cookie.match(/(?:^|;\s*)scamlens_lang=([^;]+)/);
    if (match && (match[1] === "en" || match[1] === "ta" || match[1] === "hi")) {
      return match[1] as Language;
    }
    // 2. Try localStorage
    const saved = localStorage.getItem("scamlens_lang");
    if (saved === "en" || saved === "ta" || saved === "hi") {
      return saved as Language;
    }
  } catch {
    // ignore
  }
  return null;
}

export const LanguageProvider: React.FC<{
  children: React.ReactNode;
  initialLanguage?: Language;
}> = ({ children, initialLanguage = "en" }) => {
  const [language, setLanguageState] = useState<Language>(initialLanguage);

  useEffect(() => {
    const saved = getClientSavedLanguage();
    const effective = saved || initialLanguage;
    setLanguageState(effective);
    if (typeof document !== "undefined") {
      document.documentElement.lang = effective;
      document.documentElement.setAttribute("data-lang", effective);
    }
  }, [initialLanguage]);

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem("scamlens_lang", lang);
        document.cookie = `scamlens_lang=${lang}; path=/; max-age=31536000; SameSite=Lax`;
        document.documentElement.lang = lang;
        document.documentElement.setAttribute("data-lang", lang);
      } catch {
        // ignore
      }
    }
  }, []);

  const t = useMemo(() => {
    return (path: string, params?: Record<string, string | number>): string => {
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
          current = typeof fallback === "string" ? fallback : path;
          break;
        }
      }

      let result = typeof current === "string" ? current : path;

      if (params && typeof result === "string") {
        for (const [k, v] of Object.entries(params)) {
          result = result.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
        }
      }

      return result;
    };
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useT = () => useContext(LanguageContext);
