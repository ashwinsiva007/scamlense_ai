import React from "react";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "rectangular" | "circular";
  width?: string | number;
  height?: string | number;
}

export function Skeleton({
  variant = "rectangular",
  width,
  height,
  className = "",
  style,
  ...props
}: SkeletonProps) {
  const variantStyles = {
    text: "h-4 rounded-md",
    rectangular: "rounded-xl",
    circular: "rounded-full",
  };

  return (
    <div
      aria-hidden="true"
      className={`bg-slate-200/70 animate-pulse motion-reduce:animate-none ${variantStyles[variant]} ${className}`}
      style={{
        width,
        height,
        ...style,
      }}
      {...props}
    />
  );
}
