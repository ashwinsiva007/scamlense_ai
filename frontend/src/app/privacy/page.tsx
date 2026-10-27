"use client";

import React from "react";
import {
  Lock,
  EyeOff,
  Server,
  HardDrive,
  ShieldCheck,
  Cloud,
  CheckCircle2,
  FileCheck2,
} from "lucide-react";
import { useT } from "@/context/LanguageContext";

export default function PrivacyPage() {
  const { t } = useT();

  const policies = [
    {
      title: t("privacy.policy1Title"),
      badge: t("privacy.policy1Badge"),
      desc: t("privacy.policy1Desc"),
      icon: <HardDrive className="w-5 h-5 text-primary" />,
    },
    {
      title: t("privacy.policy2Title"),
      badge: t("privacy.policy2Badge"),
      desc: t("privacy.policy2Desc"),
      icon: <EyeOff className="w-5 h-5 text-primary" />,
    },
    {
      title: t("privacy.policy3Title"),
      badge: t("privacy.policy3Badge"),
      desc: t("privacy.policy3Desc"),
      icon: <Lock className="w-5 h-5 text-primary" />,
    },
    {
      title: t("privacy.policy4Title"),
      badge: t("privacy.policy4Badge"),
      desc: t("privacy.policy4Desc"),
      icon: <Server className="w-5 h-5 text-primary" />,
    },
  ];

  const comparisonRows = [
    {
      feature: t("privacy.featureDataTransmission"),
      cloud: t("privacy.cloudDataTransmission"),
      local: t("privacy.localDataTransmission"),
    },
    {
      feature: t("privacy.featureDataStorage"),
      cloud: t("privacy.bothNoStorage"),
      local: t("privacy.bothNoStorage"),
    },
    {
      feature: t("privacy.featureInternetAccess"),
      cloud: t("privacy.cloudVerifiers"),
      local: t("privacy.localVerifiers"),
    },
    {
      feature: t("privacy.featureModelInference"),
      cloud: t("privacy.cloudModelInference"),
      local: t("privacy.localModelInference"),
    },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-16 space-y-12">
      {/* Page Header */}
      <div className="text-center space-y-3 max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>{t("privacy.badge")}</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          {t("privacy.title")}
        </h1>
        <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-medium">
          {t("privacy.subtitle")}
        </p>
      </div>

      {/* Cloud vs Local Mode Comparison Table */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-200 space-y-6 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">
          {t("privacy.comparisonTitle")}
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs sm:text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="py-3 px-3 font-bold text-slate-700 w-1/4"></th>
                <th className="py-3 px-3 font-bold text-info-dark w-3/8">
                  <div className="flex items-center gap-1.5">
                    <Cloud className="w-4 h-4 text-info" />
                    <span>{t("privacy.cloudMode")}</span>
                  </div>
                </th>
                <th className="py-3 px-3 font-bold text-primary w-3/8">
                  <div className="flex items-center gap-1.5">
                    <Server className="w-4 h-4 text-primary" />
                    <span>{t("privacy.localMode")}</span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {comparisonRows.map((row, i) => (
                <tr key={i} className="hover:bg-slate-50/50">
                  <td className="py-3.5 px-3 font-semibold text-slate-800">
                    {row.feature}
                  </td>
                  <td className="py-3.5 px-3 text-slate-600">
                    {row.cloud}
                  </td>
                  <td className="py-3.5 px-3 text-slate-600">
                    {row.local}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Privacy Guarantees Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {policies.map((p, idx) => (
          <div
            key={idx}
            className="glass-panel p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center">
                {p.icon}
              </div>
              <span className="text-[11px] font-semibold text-slate-500 font-mono">
                {p.badge}
              </span>
            </div>
            <h2 className="text-base font-bold text-slate-900">{p.title}</h2>
            <p className="text-xs text-slate-600 leading-relaxed font-medium">{p.desc}</p>
          </div>
        ))}
      </div>

      {/* Open Source Audit Commitment Box */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 space-y-2 shadow-sm">
        <div className="flex items-center gap-2 text-primary">
          <FileCheck2 className="w-5 h-5" />
          <h2 className="text-base font-bold text-slate-900">
            {t("privacy.guaranteeBoxTitle")}
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed font-medium">
          {t("privacy.guaranteeBoxDesc")}
        </p>
      </div>
    </div>
  );
}
