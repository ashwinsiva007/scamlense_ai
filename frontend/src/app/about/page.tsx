"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Github,
  Heart,
  PlusCircle,
  FileCode,
  Check,
  X,
  ExternalLink,
  BookOpen,
} from "lucide-react";
import { useT } from "@/context/LanguageContext";
import { Button } from "@/components/ui/Button";

export default function AboutPage() {
  const { t } = useT();

  const comparison = [
    {
      tool: "ScamLens (This Project)",
      isUs: true,
      openSource: true,
      tamilHindi: true,
      localMode: true,
      quotedEvidence: true,
      publishedAccuracy: true,
      communityRules: true,
    },
    {
      tool: "Norton Genie",
      isUs: false,
      openSource: false,
      tamilHindi: false,
      localMode: false,
      quotedEvidence: false,
      publishedAccuracy: false,
      communityRules: false,
    },
    {
      tool: "Trend Micro ScamCheck",
      isUs: false,
      openSource: false,
      tamilHindi: false,
      localMode: false,
      quotedEvidence: false,
      publishedAccuracy: false,
      communityRules: false,
    },
    {
      tool: "ScamDekho",
      isUs: false,
      openSource: false,
      tamilHindi: false,
      localMode: false,
      quotedEvidence: false,
      publishedAccuracy: false,
      communityRules: false,
    },
    {
      tool: "Seerie",
      isUs: false,
      openSource: false,
      tamilHindi: false,
      localMode: false,
      quotedEvidence: false,
      publishedAccuracy: false,
      communityRules: false,
    },
    {
      tool: "ScamRakshak",
      isUs: false,
      openSource: false,
      tamilHindi: false,
      localMode: false,
      quotedEvidence: false,
      publishedAccuracy: false,
      communityRules: false,
    },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 sm:py-16 space-y-12">
      {/* Header */}
      <div className="text-center space-y-3 max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
          <Heart className="w-3.5 h-3.5 text-danger" />
          <span>{t("about.badge")}</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          {t("about.title")}
        </h1>
        <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-medium">
          {t("about.subtitle")}
        </p>
      </div>

      {/* Mission Section */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-lg font-bold text-slate-900">{t("about.missionTitle")}</h2>
        <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
          {t("about.missionDesc")}
        </p>
      </div>

      {/* Honest Comparison Table */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-5">
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            {t("about.comparisonHeader")}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {t("about.comparisonSub")}
          </p>
        </div>

        <div className="overflow-x-auto -mx-6 sm:mx-0">
          <table className="w-full text-left border-collapse min-w-[620px]">
            <thead>
              <tr className="border-b border-slate-200 text-[11px] uppercase tracking-wider text-slate-500 bg-slate-50/60">
                <th className="py-3 px-4 font-bold">{t("about.tableTool")}</th>
                <th className="py-3 px-3 font-bold text-center">{t("about.tableTamilHindi")}</th>
                <th className="py-3 px-3 font-bold text-center">{t("about.tableOpenSource")}</th>
                <th className="py-3 px-3 font-bold text-center">{t("about.tableLocalMode")}</th>
                <th className="py-3 px-3 font-bold text-center">{t("about.tableQuotedEvidence")}</th>
                <th className="py-3 px-3 font-bold text-center">{t("about.tablePublishedAccuracy")}</th>
                <th className="py-3 px-3 font-bold text-center">{t("about.tableCommunityRules")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs font-medium">
              {comparison.map((item, idx) => (
                <tr
                  key={idx}
                  className={item.isUs ? "bg-primary/5 font-bold text-slate-900" : "text-slate-700 hover:bg-slate-50"}
                >
                  <td className="py-3.5 px-4 flex items-center gap-1.5">
                    {item.isUs && <ShieldCheck className="w-4 h-4 text-primary shrink-0" />}
                    <span>{item.tool}</span>
                  </td>
                  <td className="py-3.5 px-3 text-center">
                    {item.tamilHindi ? (
                      <Check className="w-4 h-4 text-primary mx-auto" />
                    ) : (
                      <X className="w-4 h-4 text-slate-300 mx-auto" />
                    )}
                  </td>
                  <td className="py-3.5 px-3 text-center">
                    {item.openSource ? (
                      <Check className="w-4 h-4 text-primary mx-auto" />
                    ) : (
                      <X className="w-4 h-4 text-slate-300 mx-auto" />
                    )}
                  </td>
                  <td className="py-3.5 px-3 text-center">
                    {item.localMode ? (
                      <Check className="w-4 h-4 text-primary mx-auto" />
                    ) : (
                      <X className="w-4 h-4 text-slate-300 mx-auto" />
                    )}
                  </td>
                  <td className="py-3.5 px-3 text-center">
                    {item.quotedEvidence ? (
                      <Check className="w-4 h-4 text-primary mx-auto" />
                    ) : (
                      <X className="w-4 h-4 text-slate-300 mx-auto" />
                    )}
                  </td>
                  <td className="py-3.5 px-3 text-center">
                    {item.publishedAccuracy ? (
                      <Check className="w-4 h-4 text-primary mx-auto" />
                    ) : (
                      <X className="w-4 h-4 text-slate-300 mx-auto" />
                    )}
                  </td>
                  <td className="py-3.5 px-3 text-center">
                    {item.communityRules ? (
                      <Check className="w-4 h-4 text-primary mx-auto" />
                    ) : (
                      <X className="w-4 h-4 text-slate-300 mx-auto" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Community Contribution Section */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <FileCode className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-bold text-slate-900">
            {t("about.communityTitle")}
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-slate-600 font-medium">
          {t("about.communityDesc")}
        </p>

        <div className="pt-4 flex flex-wrap gap-3">
          <a
            href="https://github.com/dharshika1814-collab/scamlensAI"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-black text-white text-xs font-semibold shadow-sm transition-all"
          >
            <Github className="w-4 h-4" />
            <span>{t("about.githubBtn")}</span>
          </a>

          <Link
            href="/benchmarks"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 text-xs font-semibold shadow-sm transition-all"
          >
            <BookOpen className="w-4 h-4 text-primary" />
            <span>{t("about.contributeBtn")}</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
