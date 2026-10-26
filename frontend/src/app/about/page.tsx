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
import { Button } from "@/components/ui/Button";

export default function AboutPage() {
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
          <span>Public Interest Technology</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          About ScamLens
        </h1>
        <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-medium">
          An open-source fraud defense engine built to protect everyday families, parents, and digital citizens from modern social engineering.
        </p>
      </div>

      {/* Why We Built It */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-lg font-bold text-slate-900">Why We Built ScamLens</h2>
        <div className="space-y-3 text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
          <p>
            India has seen a phenomenal democratization of digital payments through UPI and instant mobile messaging. However, this transition has been accompanied by an aggressive surge in predatory digital fraud: fake job offers demanding refundable deposits, forged payment screenshots used to deceive small shopkeepers, and threatening SMS alerts claiming electricity or bank accounts will be disconnected.
          </p>
          <p>
            Elders and non-English speakers face an acute linguistic disadvantage. Most cybersecurity software only operates in English, provides black-box &quot;safe&quot; declarations that breed false security, or requires uploading sensitive personal documents to proprietary commercial servers.
          </p>
          <p>
            <strong>ScamLens was created to dismantle this barrier.</strong> By combining multilingual multimodal perception (English, Tamil, Hindi) with an auditable open-source rule engine and zero-retention privacy guarantees, anyone can evaluate suspicious messages and generate shareable Family Alert cards for relatives.
          </p>
        </div>
      </div>

      {/* Honest Comparison Table */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-5">
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            How ScamLens Compares
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            An honest comparison with popular existing scam and message checkers.
          </p>
        </div>

        <div className="overflow-x-auto -mx-6 sm:mx-0">
          <table className="w-full text-left border-collapse min-w-[620px]">
            <thead>
              <tr className="border-b border-slate-200 text-[11px] uppercase tracking-wider text-slate-500 bg-slate-50/60">
                <th className="py-3 px-4 font-bold">Platform</th>
                <th className="py-3 px-3 font-bold text-center">Tamil &amp; Hindi First</th>
                <th className="py-3 px-3 font-bold text-center">Open-Source</th>
                <th className="py-3 px-3 font-bold text-center">Private Local Mode</th>
                <th className="py-3 px-3 font-bold text-center">Quoted Evidence</th>
                <th className="py-3 px-3 font-bold text-center">Published Accuracy</th>
                <th className="py-3 px-3 font-bold text-center">Community Rules</th>
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

      {/* How to Add a Rule Pack Section */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <FileCode className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-bold text-slate-900">
            How to Add a Community Rule Pack
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-slate-600 font-medium">
          ScamLens is powered by deterministic YAML rule packs. Any developer, security researcher, or community advocate can contribute new fraud pattern detectors:
        </p>

        <div className="space-y-3 pt-2">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
            <span className="text-xs font-bold text-slate-900 font-mono">
              1. Create a Rule File
            </span>
            <p className="text-xs text-slate-600">
              Create a new YAML file under `backend/rules/&lt;vector_name&gt;.yaml` (e.g., `utility_threats.yaml`).
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
            <span className="text-xs font-bold text-slate-900 font-mono">
              2. Define Patterns &amp; Weights
            </span>
            <pre className="text-[11px] font-mono bg-slate-900 text-slate-200 p-3 rounded-lg overflow-x-auto">
{`name: utility_threats
category: urgency_threat
rules:
  - id: ELECTRICITY_POWER_CUT_TONIGHT
    label: Threat of Tonight's Electricity Disconnection
    weight: 35.0
    patterns:
      - "power will be disconnected tonight"
      - "electricity bill unpaid"
    evidence_template: "Unsolicited threat to cut off utilities"`}
            </pre>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
            <span className="text-xs font-bold text-slate-900 font-mono">
              3. Run Test Suite
            </span>
            <p className="text-xs text-slate-600">
              Run `pytest backend/tests/test_rule_packs.py` to verify deterministic evaluation and ensure zero regressions.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
            <span className="text-xs font-bold text-slate-900 font-mono">
              4. Submit a Pull Request
            </span>
            <p className="text-xs text-slate-600">
              Submit your contribution to the open-source repository on GitHub to protect thousands of users!
            </p>
          </div>
        </div>

        <div className="pt-4 flex flex-wrap gap-3">
          <a
            href="https://github.com/dharshika1814-collab/scamlensAI"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-black text-white text-xs font-semibold shadow-sm transition-all"
          >
            <Github className="w-4 h-4" />
            <span>GitHub Repository</span>
          </a>

          <Link
            href="/benchmarks"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 text-xs font-semibold shadow-sm transition-all"
          >
            <BookOpen className="w-4 h-4 text-primary" />
            <span>View Benchmark Data</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
