"use client";

import React from "react";
import Link from "next/link";
import {
  Lock,
  Eye,
  Network,
  ShieldAlert,
  CheckCircle2,
  Terminal,
  ShieldCheck,
  FileCheck2,
  ArrowRight,
} from "lucide-react";
import { useT } from "@/context/LanguageContext";
import { Button } from "@/components/ui/Button";

export default function HowItWorksPage() {
  const { t } = useT();

  const pipelineSteps = [
    {
      num: "01",
      title: t("howItWorks.step1Title"),
      tag: t("howItWorks.step1Tag"),
      desc: t("howItWorks.step1Desc"),
      icon: <Lock className="w-5 h-5 text-primary" />,
    },
    {
      num: "02",
      title: t("howItWorks.step2Title"),
      tag: t("howItWorks.step2Tag"),
      desc: t("howItWorks.step2Desc"),
      icon: <Eye className="w-5 h-5 text-primary" />,
    },
    {
      num: "03",
      title: t("howItWorks.step3Title"),
      tag: t("howItWorks.step3Tag"),
      desc: t("howItWorks.step3Desc"),
      icon: <Network className="w-5 h-5 text-info" />,
    },
    {
      num: "04",
      title: t("howItWorks.step4Title"),
      tag: t("howItWorks.step4Tag"),
      desc: t("howItWorks.step4Desc"),
      icon: <ShieldAlert className="w-5 h-5 text-warning" />,
    },
    {
      num: "05",
      title: t("howItWorks.step5Title"),
      tag: t("howItWorks.step5Tag"),
      desc: t("howItWorks.step5Desc"),
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-700" />,
    },
  ];

  const pillars = [
    {
      title: t("howItWorks.pillar1Title"),
      desc: t("howItWorks.pillar1Desc"),
      icon: <FileCheck2 className="w-5 h-5 text-primary" />,
    },
    {
      title: t("howItWorks.pillar2Title"),
      desc: t("howItWorks.pillar2Desc"),
      icon: <ShieldAlert className="w-5 h-5 text-danger" />,
    },
    {
      title: t("howItWorks.pillar3Title"),
      desc: t("howItWorks.pillar3Desc"),
      icon: <Lock className="w-5 h-5 text-emerald-700" />,
    },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-16 space-y-12">
      {/* Page Header */}
      <div className="text-center space-y-3 max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
          <Terminal className="w-3.5 h-3.5" />
          <span>{t("howItWorks.badge")}</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          {t("howItWorks.title")}
        </h1>
        <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-medium">
          {t("howItWorks.subtitle")}
        </p>
      </div>

      {/* 5-Step Pipeline */}
      <div className="space-y-4">
        {pipelineSteps.map((step, idx) => (
          <div
            key={step.num}
            className="glass-panel p-5 sm:p-6 rounded-2xl border border-slate-200/90 shadow-sm hover:shadow-md transition-shadow relative"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center shrink-0">
                  {step.icon}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-slate-400">
                      STEP {step.num}
                    </span>
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                      {step.tag}
                    </span>
                  </div>
                  <h2 className="text-base font-bold text-slate-900">{step.title}</h2>
                </div>
              </div>

              {idx < pipelineSteps.length - 1 && (
                <div className="hidden sm:flex items-center text-slate-300">
                  <ArrowRight className="w-5 h-5" />
                </div>
              )}
            </div>

            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed font-medium pt-3">
              {step.desc}
            </p>
          </div>
        ))}
      </div>

      {/* Architectural Philosophy & Pillars */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 space-y-6 shadow-sm">
        <div className="space-y-2 text-center max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>{t("howItWorks.philosophyBadge")}</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
            {t("howItWorks.philosophyTitle")}
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed font-medium">
            {t("howItWorks.philosophySubtitle")}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          {pillars.map((pillar, i) => (
            <div
              key={i}
              className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2"
            >
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center shrink-0 shadow-sm">
                  {pillar.icon}
                </div>
                <h3 className="text-sm font-bold text-slate-900">{pillar.title}</h3>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                {pillar.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom CTA Banner */}
      <div className="rounded-2xl border-2 border-primary/30 bg-primary/5 p-6 sm:p-8 text-center space-y-4 shadow-sm">
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
          {t("howItWorks.bottomBannerTitle")}
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 max-w-xl mx-auto font-medium">
          {t("howItWorks.bottomBannerDesc")}
        </p>
        <Link href="/" className="inline-block">
          <Button
            variant="primary"
            size="md"
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            {t("howItWorks.tryAnalyzerBtn")}
          </Button>
        </Link>
      </div>
    </div>
  );
}
