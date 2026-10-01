"use client";

import React, { createContext, useContext } from "react";

export interface NavigationContextValue {
  currentPath: string;
  navigateTo: (href: string) => void;
}

export const NavigationContext = createContext<NavigationContextValue>({
  currentPath: "/",
  navigateTo: () => {},
});

export const useInstantNav = () => useContext(NavigationContext);
