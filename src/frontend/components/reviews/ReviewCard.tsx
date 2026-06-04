'use client';

import { Star, User } from 'lucide-react';

interface ReviewCardProps {
  user_name?: string;
  rating: number;
  title?: string;
  comment?: string;
  created_at: string;
}

export function ReviewCard({ user_name, rating, title, comment, created_at }: ReviewCardProps) {
  return (
    <div className="rounded-lg border p-4 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
            {user_name?.charAt(0) || <User className="h-4 w-4" />}
          </div>
          <span className="text-sm font-medium">{user_name || 'Anonymous'}</span>
        </div>
        <div className="flex items-center gap-0.5">
          {Array.from({ length: 5 }, (_, i) => (
            <Star
              key={i}
              className={`h-4 w-4 ${i < rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-200'}`}
            />
          ))}
        </div>
      </div>

      {title && <p className="font-medium text-sm">{title}</p>}
      {comment && <p className="text-sm text-muted-foreground">{comment}</p>}

      {created_at && (
        <p className="text-xs text-muted-foreground">
          {new Date(created_at).toLocaleDateString()}
        </p>
      )}
    </div>
  );
}
