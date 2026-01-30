import {createContext, useContext} from "react";
import {type AuthState} from "../context/AuthContext";

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
export const AuthContext = createContext<AuthState | null>(null);