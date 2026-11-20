"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface AuthContextType {
  user: {
    user_id: string | null;
    username: string | null;
    email: string | null;
    roles: string[];
  } | null;
  isAuthenticated: boolean;
  login: (targetUrl?: string) => Promise<void>;
  logout: () => Promise<void>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<{
    user_id: string | null;
    username: string | null;
    email: string | null;
    roles: string[];
  } | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for token in localStorage on mount
    const token = localStorage.getItem("id_token");
    const profile = localStorage.getItem("user_profile");
    if (token && profile) {
      const profileData = JSON.parse(profile);
      setUser({
        user_id: profileData.sub || null,
        username: profileData.preferred_username || null,
        email: profileData.email || null,
        roles: profileData.realm_access?.roles || [],
      });
      setIsAuthenticated(true);
    }
    setLoading(false);
  }, []);

  const login = async (targetUrl?: string) => {
    // PKCE flow
    const verifier = generateCodeVerifier();
    const challenge = await generateCodeChallenge(verifier);

    // Store verifier in sessionStorage for callback
    sessionStorage.setItem("pkce_verifier", verifier);

    const codeChallenge = challenge; // from generateCodeChallenge

    const keycloakUrl = import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8080";
    const realm = import.meta.env.VITE_KEYCLOAK_REALM || "beacon-hub";
    const clientId = import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "beacon-frontend";

    const redirectUri = `${window.location.origin}/api/v1/auth/callback`;
    const state = btoa(JSON.stringify({
      targetUrl: targetUrl || window.location.pathname,
      verifier,
    }));

    const authUrl = new URL(`${keycloakUrl}/realms/${realm}/protocol/openid-connect/auth`);
    authUrl.searchParams.set("client_id", clientId);
    authUrl.searchParams.set("redirect_uri", redirectUri);
    authUrl.searchParams.set("response_type", "code");
    authUrl.searchParams.set("scope", "openid profile email");
    authUrl.searchParams.set("code_challenge", codeChallenge);
    authUrl.searchParams.set("code_challenge_method", "S256");
    authUrl.searchParams.set("state", state);
    authUrl.searchParams.set("prompt", "login");

    window.location.href = authUrl.toString();
  };

  const logout = async () => {
    localStorage.removeItem("id_token");
    localStorage.removeItem("user_profile");
    sessionStorage.removeItem("pkce_verifier");
    setUser(null);
    setIsAuthenticated(false);
    window.location.href = "/api/v1/auth/logout";
  };

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated,
      login,
      logout,
      loading,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
};
