import React from "react";

export function Card({ children, className = "", ...props }) {
  return (
    <div
      className={`rounded-lg border border-gray-300 bg-white shadow-md p-4 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardContent({ children, className = "", ...props }) {
  return (
    <div className={`p-2 ${className}`} {...props}>
      {children}
    </div>
  );
}
