import type { Metadata } from "next";
import { Inter, Noto_Sans_Tamil, Noto_Sans_Devanagari } from "next/font/google";
import { cookies } from "next/headers";
import "./globals.css";
import { Language, LanguageProvider } from "@/context/LanguageContext";
import { ToastProvider } from "@/components/ui/Toast";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const notoSansTamil = Noto_Sans_Tamil({
  subsets: ["tamil"],
  variable: "--font-noto-tamil",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const notoSansDevanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  variable: "--font-noto-devanagari",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "ScamLens • Explainable, Privacy-First Scam Detection",
  description:
    "Verify suspicious offer letters, delivery SMS, and payment screenshots with transparent red flags, quoted evidence, and shareable Family Alert cards.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = cookies();
  const rawLang = cookieStore.get("scamlens_lang")?.value;
  const initialLang: Language = (rawLang === "ta" || rawLang === "hi") ? rawLang : "en";

  return (
    <html
      lang={initialLang}
      data-lang={initialLang}
      className={`${inter.variable} ${notoSansTamil.variable} ${notoSansDevanagari.variable}`}
    >
      <body className="font-sans antialiased bg-background text-text min-h-screen flex flex-col selection:bg-primary-light selection:text-primary">
        <LanguageProvider initialLanguage={initialLang}>
          <ToastProvider>
            <Navbar />
            <main className="flex-1">{children}</main>
            <Footer />
          </ToastProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
