"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";

/** Resolves the Clerk session token used for backend calls. */
export function useAuthToken() {
  const { getToken, isLoaded } = useAuth();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded) return;
    let active = true;
    void getToken().then((next) => {
      if (active) setToken(next);
    });
    return () => {
      active = false;
    };
  }, [getToken, isLoaded]);

  return { token, isReady: isLoaded && token !== null };
}
