'use client';

import { useState } from 'react';
import { Heart } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useLocale } from 'next-intl';
import { useRouter } from 'next/navigation';

interface WishlistButtonProps {
  tourId: string;
  initialWishlisted?: boolean;
  className?: string;
}

export function WishlistButton({ tourId, initialWishlisted = false, className = '' }: WishlistButtonProps) {
  const { token, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const locale = useLocale();
  const [wishlisted, setWishlisted] = useState(initialWishlisted);
  const [animating, setAnimating] = useState(false);

  const handleToggle = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      router.push(`/${locale}/auth`);
      return;
    }

    setAnimating(true);
    try {
      if (wishlisted) {
        await api.delete(`/wishlist/${tourId}`);
        setWishlisted(false);
      } else {
        await api.post(`/wishlist/${tourId}`, {});
        setWishlisted(true);
      }
    } catch { /* ignore */ }
    setAnimating(false);
  };

  return (
    <button
      onClick={handleToggle}
      disabled={animating}
      className={`p-2 rounded-full transition-colors ${
        wishlisted ? 'text-red-500' : 'text-gray-400 hover:text-red-400'
      } ${className}`}
    >
      <Heart className={`h-5 w-5 ${wishlisted ? 'fill-current' : ''}`} />
    </button>
  );
}
