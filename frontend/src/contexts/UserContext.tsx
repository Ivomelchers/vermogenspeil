import { createContext, useContext, type ReactNode } from "react";

import { useAuth, type UseAuthReturn } from "../hooks/useAuth";

const UserContext = createContext<UseAuthReturn | null>(null);

export function UserProvider({ children }: { children: ReactNode }) {
  const auth = useAuth();
  return <UserContext.Provider value={auth}>{children}</UserContext.Provider>;
}

export function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUser must be used within UserProvider");
  }
  return context;
}
