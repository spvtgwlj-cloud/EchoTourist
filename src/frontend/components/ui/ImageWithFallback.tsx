'use client';

import { useState } from 'react';

interface ImageWithFallbackProps {
  src: string;
  alt: string;
  className?: string;
}

/**
 * 带加载失败回退的图片组件。
 * 当图片加载失败时，显示一个渐变背景 + 产品名称缩写。
 */
export function ImageWithFallback({ src, alt, className = '' }: ImageWithFallbackProps) {
  const [failed, setFailed] = useState(false);

  if (failed || !src) {
    // 从 alt 提取首字符用于显示
    const initial = alt?.charAt(0) || '?';
    return (
      <div className={`flex items-center justify-center bg-gradient-to-br from-primary/20 via-primary/10 to-accent/10 ${className}`}>
        <span className="text-6xl font-bold text-primary/30 select-none">
          {initial}
        </span>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      className={className}
      onError={() => setFailed(true)}
    />
  );
}
