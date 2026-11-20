"use client";

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export const useAuthCallback = () => {
  const navigate = useNavigate();
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");

    if (!code) {
      setAuthenticated(false);
      navigate("/");
      return;
    }

    const parsedState = JSON.parse(atob(state || "null"));
    const storedVerifier = sessionStorage.getItem("pkce_verifier");

    if (!storedVerifier) {
      setAuthenticated(false);
      navigate("/");
      return;
    }

    fetch("/api/v1/auth/callback", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        code,
        verifier: storedVerifier,
        state: parsedState,
      }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Token exchange failed");
        }
        const data = await res.json();
        localStorage.setItem("id_token", data.id_token);
        localStorage.setItem("user_profile", JSON.stringify(data.user));
        setAuthenticated(true);
        navigate(parsedState.targetUrl || "/");
      })
      .catch((err) => {
        console.error("Auth callback error:", err);
        setAuthenticated(false);
        navigate("/");
      });
  }, [navigate]);

  return authenticated;
};
