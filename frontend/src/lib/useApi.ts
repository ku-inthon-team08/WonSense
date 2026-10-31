"use client";

import { useEffect, useState } from "react";

type State<T> = { key: string | null; data?: T; error?: Error };

/**
 * key가 바뀔 때마다 fetcher를 다시 부르는 클라이언트 fetch 훅. key가 null이면 부르지 않는다.
 * 이전 key의 응답이 늦게 와도 버린다 (AbortController).
 */
export function useApi<T>(key: string | null, fetcher: (signal: AbortSignal) => Promise<T>) {
  const [state, setState] = useState<State<T>>({ key: null });

  useEffect(() => {
    if (key === null) return;
    const controller = new AbortController();
    fetcher(controller.signal).then(
      (data) => setState({ key, data }),
      (error: Error) => {
        if (!controller.signal.aborted) setState({ key, error });
      },
    );
    return () => controller.abort();
    // fetcher는 key로 결정되므로 key만 의존한다
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const current = state.key === key;
  return {
    data: current ? state.data : undefined,
    error: current ? state.error : undefined,
    loading: key !== null && !current,
  };
}
