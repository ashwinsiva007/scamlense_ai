"use client";

import React, { useRef, useState } from "react";
import { ShieldCheck, Download, Copy, Check, Share2 } from "lucide-react";
import { toPng } from "html-to-image";
import { FamilyAlert } from "@/lib/api";
import { Language } from "@/context/LanguageContext";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";

interface FamilyAlertCardProps {
  alert: FamilyAlert;
  language: Language;
  labels: {
    header: string;
    sub: string;
    watermark: string;
    downloadPng: string;
    copyAlert: string;
    shareWhatsApp: string;
    copied: string;
  };
}

export function FamilyAlertCard({ alert, language, labels }: FamilyAlertCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const { toast } = useToast();

  const title = alert?.title || "Family Fraud Safety Alert";
  const body = alert?.body || "Exercise high caution before sharing credentials or money.";
  const tips = Array.isArray(alert?.tips) ? alert.tips : [];

  const formattedShareText = `${title}\n\n${body}\n\nKey Safety Rules:\n${tips
    .map((tip) => `• ${tip}`)
    .join("\n")}\n\n— ScamLens: Verify before you act (https://scamlens.org)`;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formattedShareText);
      setIsCopied(true);
      toast(labels.copied, "success");
      setTimeout(() => setIsCopied(false), 2000);
    } catch {
      toast("Could not copy to clipboard", "error");
    }
  };

  const handleShareWhatsApp = () => {
    const url = `https://wa.me/?text=${encodeURIComponent(formattedShareText)}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const handleDownloadPng = async () => {
    if (!cardRef.current) return;
    setIsDownloading(true);

    try {
      // Small delay to allow any pending layout stabilization
      await new Promise((resolve) => setTimeout(resolve, 80));

      const dataUrl = await toPng(cardRef.current, {
        cacheBust: true,
        pixelRatio: 2.5,
        backgroundColor: "#FFFFFF",
        style: {
          transform: "scale(1)",
        },
      });

      const link = document.createElement("a");
      link.download = `scamlens-family-alert-${language}-${Date.now()}.png`;
      link.href = dataUrl;
      link.click();
      toast("Image saved successfully!", "success");
    } catch (err) {
      console.error("Failed to generate image", err);
      toast("Failed to download image. Try copying text instead.", "error");
    } finally {
      setIsDownloading(false);
    }
  };

  // Font family based on language for flawless rasterization
  const getFontFamily = () => {
    if (language === "ta") return "var(--font-noto-tamil), sans-serif";
    if (language === "hi") return "var(--font-noto-devanagari), sans-serif";
    return "var(--font-inter), sans-serif";
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-warning shrink-0" />
            <span>{labels.header}</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">{labels.sub}</p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2 pt-2 sm:pt-0">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleDownloadPng}
            isLoading={isDownloading}
            leftIcon={<Download className="w-3.5 h-3.5" />}
          >
            {labels.downloadPng}
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleCopy}
            leftIcon={
              isCopied ? (
                <Check className="w-3.5 h-3.5 text-primary" />
              ) : (
                <Copy className="w-3.5 h-3.5 text-slate-500" />
              )
            }
          >
            {isCopied ? labels.copied : labels.copyAlert}
          </Button>

          <Button
            type="button"
            variant="primary"
            size="sm"
            onClick={handleShareWhatsApp}
            leftIcon={<Share2 className="w-3.5 h-3.5" />}
            className="bg-[#25D366] hover:bg-[#20BD5A] border-[#25D366] text-white"
          >
            {labels.shareWhatsApp}
          </Button>
        </div>
      </div>

      {/* The Printable / Downloadable Card Node */}
      <div
        ref={cardRef}
        className="rounded-2xl border-2 border-warning/40 bg-gradient-to-br from-amber-50/90 via-orange-50/50 to-white p-6 sm:p-7 shadow-md space-y-4 text-slate-900"
        style={{ fontFamily: getFontFamily() }}
      >
        {/* Card Header & Brand Logo */}
        <div className="flex items-center justify-between border-b border-warning/20 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-primary text-white flex items-center justify-center font-bold text-sm shadow-sm">
              SL
            </div>
            <div>
              <span className="font-extrabold text-sm tracking-tight text-slate-900 block leading-tight">
                ScamLens
              </span>
              <span className="text-[10px] text-slate-500 block leading-tight">
                Community Fraud Defense
              </span>
            </div>
          </div>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-warning-light text-warning-dark border border-warning/30">
            Family Alert
          </span>
        </div>

        {/* Alert Title */}
        <h4 className="text-base sm:text-lg font-extrabold text-slate-900 leading-snug">
          {title}
        </h4>

        {/* Alert Body */}
        <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
          {body}
        </p>

        {/* Actionable Tips */}
        <div className="bg-white/80 rounded-xl p-4 border border-warning/20 space-y-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-warning-dark block">
            Key Precautions:
          </span>
          <ul className="space-y-1.5 text-xs sm:text-sm text-slate-800">
            {tips.map((tip, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-warning mt-1.5 shrink-0" />
                <span className="font-medium">{tip}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Watermark Line */}
        <div className="flex items-center justify-between pt-2 border-t border-warning/20 text-[11px] text-slate-500">
          <span className="font-semibold text-primary">{labels.watermark}</span>
          <span>Helpline: 1930</span>
        </div>
      </div>
    </div>
  );
}
