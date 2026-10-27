"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
  resetLabel?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ScamLens component error caught:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="glass-panel rounded-2xl border border-red-200 bg-red-50/50 p-6 sm:p-8 text-center space-y-4 animate-fadeIn shadow-sm">
          <div className="w-12 h-12 rounded-xl bg-red-100 border border-red-300 flex items-center justify-center mx-auto text-red-600">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base sm:text-lg font-bold text-slate-900">
              Unable to display analysis report
            </h3>
            <p className="text-xs sm:text-sm text-slate-600 max-w-md mx-auto">
              A problem occurred while rendering this report. You can retry the analysis or upload another file.
            </p>
          </div>
          <div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={this.handleReset}
              leftIcon={<RotateCcw className="w-4 h-4 text-primary" />}
            >
              {this.props.resetLabel || "Try Again / Reset"}
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
