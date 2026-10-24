import { useEffect, useState } from 'react';

// Long enough to read the subtitle and see the frame settle. Fast GMGN answers do not skip the story.
export const DWELL_MS = 5200;

// Plays reels in film order. The current reel holds for DWELL_MS once its answer is ready.
export function useReelQueue(ids, ready) {
  const [index, setIndex] = useState(0);
  const current = ids[index];
  const isReady = current ? ready(current) : false;

  useEffect(() => {
    if (index >= ids.length || !isReady) return undefined;
    const timer = setTimeout(() => setIndex((i) => i + 1), DWELL_MS);
    return () => clearTimeout(timer);
  }, [index, isReady, ids.length]);

  return { index, waiting: index < ids.length && !isReady, finished: index >= ids.length };
}
