import { useCallback, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { eventEmitter } from "../api/api";
import {
  auth,
  getMfaToken,
  isMfaRequired,
  login,
  type Auth0TokenResponse,
} from "../api/auth";

const MIN_AUTH_LOADING_MS = import.meta.env.DEV ? 0 : 1600;

function readHasToken(): boolean {
  return Boolean(localStorage.getItem("id_token"));
}

function clearStoredTokens() {
  localStorage.removeItem("id_token");
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("rememberMe");
  localStorage.removeItem("mfa_token");
}

function storeAuth0Tokens(tokens: Auth0TokenResponse, rememberMe: boolean) {
  localStorage.setItem("id_token", tokens.id_token);
  localStorage.setItem("access_token", tokens.access_token);
  localStorage.setItem("rememberMe", rememberMe ? "true" : "false");

  if (rememberMe) {
    localStorage.setItem("refresh_token", tokens.refresh_token);
  } else {
    localStorage.removeItem("refresh_token");
  }
}

export function useAuth() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [minLoadingDone, setMinLoadingDone] = useState(MIN_AUTH_LOADING_MS === 0);
  const [hasToken, setHasToken] = useState(readHasToken);

  useEffect(() => {
    if (MIN_AUTH_LOADING_MS === 0) return;
    const timer = window.setTimeout(() => setMinLoadingDone(true), MIN_AUTH_LOADING_MS);
    return () => window.clearTimeout(timer);
  }, []);

  const meQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: auth,
    enabled: hasToken,
    retry: false,
  });

  const handleSessionExpired = useCallback(() => {
    clearStoredTokens();
    setHasToken(false);
    queryClient.removeQueries({ queryKey: ["auth", "me"] });
    navigate("/auth/login", {
      replace: true,
      state: { message: "Uw sessie is verlopen. Log opnieuw in." },
    });
  }, [navigate, queryClient]);

  const logout = useCallback(() => {
    clearStoredTokens();
    setHasToken(false);
    queryClient.removeQueries({ queryKey: ["auth", "me"] });
    navigate("/auth/login", { replace: true });
  }, [navigate, queryClient]);

  useEffect(() => {
    return eventEmitter.on("logout", handleSessionExpired);
  }, [handleSessionExpired]);

  useEffect(() => {
    if (!hasToken || !meQuery.isError) return;
    clearStoredTokens();
    setHasToken(false);
    queryClient.removeQueries({ queryKey: ["auth", "me"] });
  }, [hasToken, meQuery.isError, queryClient]);

  const completeLogin = useCallback(
    async (tokens: Auth0TokenResponse, rememberMe: boolean) => {
      storeAuth0Tokens(tokens, rememberMe);
      setHasToken(true);
      await queryClient.fetchQuery({ queryKey: ["auth", "me"], queryFn: auth });
    },
    [queryClient],
  );

  const loginMutation = useMutation({
    mutationFn: async ({
      email,
      password,
      rememberMe,
    }: {
      email: string;
      password: string;
      rememberMe: boolean;
    }) => {
      try {
        const tokens = await login({ email, password });
        await completeLogin(tokens, rememberMe);
        return { status: "authenticated" as const };
      } catch (error) {
        if (isMfaRequired(error)) {
          const mfaToken = getMfaToken(error);
          if (mfaToken) {
            localStorage.setItem("mfa_token", mfaToken);
          }
          return { status: "mfa_required" as const, rememberMe };
        }
        throw error;
      }
    },
  });

  const loginWithUsernameAndPassword = useCallback(
    async (email: string, password: string, rememberMe: boolean) => {
      return loginMutation.mutateAsync({ email, password, rememberMe });
    },
    [loginMutation],
  );

  const completeMfaLoginFlow = useCallback(
    async (tokens: Auth0TokenResponse, rememberMe: boolean) => {
      localStorage.removeItem("mfa_token");
      await completeLogin(tokens, rememberMe);
    },
    [completeLogin],
  );

  const user = meQuery.data ?? null;

  const permissions = useMemo(() => {
    if (!user) {
      return {
        isPremium: false,
        isFree: true,
        isVerified: false,
      };
    }

    return {
      isPremium: user.is_premium,
      isFree: user.subscription_tier === "free",
      isVerified: user.email_verified,
    };
  }, [user]);

  const isAuthenticated = hasToken && Boolean(user) && !meQuery.isError;
  const loading =
    !minLoadingDone ||
    loginMutation.isPending ||
    (hasToken && (meQuery.isLoading || meQuery.isFetching));

  return {
    user,
    isAuthenticated,
    permissions,
    loading,
    error: meQuery.error,
    loginWithUsernameAndPassword,
    completeMfaLoginFlow,
    logout,
    isLoggingIn: loginMutation.isPending,
  };
}

export type UseAuthReturn = ReturnType<typeof useAuth>;
