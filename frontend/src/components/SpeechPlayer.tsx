"use client";

import React, { useState, useEffect, useRef } from "react";
import { Volume2, VolumeX, Pause, Play } from "lucide-react";
import { Language } from "@/context/LanguageContext";
import { Button } from "@/components/ui/Button";

interface SpeechPlayerProps {
  text: string;
  language: Language;
  onUnavailable?: (msg: string) => void;
  className?: string;
  labels: {
    readAloud: string;
    playing: string;
    unavailable: string;
  };
}

export function SpeechPlayer({
  text,
  language,
  onUnavailable,
  className = "",
  labels,
}: SpeechPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const langCode = language === "ta" ? "ta-IN" : language === "hi" ? "hi-IN" : "en-IN";

  useEffect(() => {
    if (typeof window !== "undefined" && !("speechSynthesis" in window)) {
      setIsSupported(false);
    }

    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handleToggleSpeech = () => {
    if (!isSupported || typeof window === "undefined" || !("speechSynthesis" in window)) {
      onUnavailable?.(labels.unavailable);
      return;
    }

    const synth = window.speechSynthesis;

    if (isPlaying) {
      synth.cancel();
      setIsPlaying(false);
      return;
    }

    // Cancel any active speech before starting new
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langCode;
    utterance.rate = 0.95; // Slightly slower for clarity
    utterance.pitch = 1.0;

    // Find best voice match if available
    const voices = synth.getVoices();
    const matchedVoice = voices.find((v) => v.lang.toLowerCase().startsWith(language));
    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    utterance.onstart = () => {
      setIsPlaying(true);
    };

    utterance.onend = () => {
      setIsPlaying(false);
    };

    utterance.onerror = (e) => {
      setIsPlaying(false);
      if (e.error !== "canceled") {
        onUnavailable?.(labels.unavailable);
      }
    };

    utteranceRef.current = utterance;
    synth.speak(utterance);
  };

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={handleToggleSpeech}
      leftIcon={isPlaying ? <VolumeX className="w-4 h-4 text-primary" /> : <Volume2 className="w-4 h-4 text-slate-600" />}
      className={className}
      aria-label={isPlaying ? labels.playing : labels.readAloud}
    >
      {isPlaying ? labels.playing : labels.readAloud}
    </Button>
  );
}
