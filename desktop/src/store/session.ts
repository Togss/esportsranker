import { create } from "zustand";

type SessionState = {
  storeId: string; // debug ID so we can check if both screens share one store
  accessToken: string | null;
  isLoggedIn: boolean;
  loginWithDeviceCode: (code: string) => void;
  logout: () => void;
};

export const useSessionStore = create<SessionState>((set) => ({
  storeId: "SESSION_STORE_SINGLETON",
  accessToken: null,
  isLoggedIn: false,

  loginWithDeviceCode: (code: string) => {
    if (code && code.trim().length > 0) {
      const fakeToken = "mock_access_token_" + code.trim();
      set({
        accessToken: fakeToken,
        isLoggedIn: true,
      });
    } else {
      console.warn("No device code entered");
    }
  },

  logout: () => {
    set({
      accessToken: null,
      isLoggedIn: false,
    });
  },
}));