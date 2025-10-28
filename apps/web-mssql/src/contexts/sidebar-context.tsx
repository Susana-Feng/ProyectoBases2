import { createContext, useContext, useState } from "react"

interface SidebarContextType {
  hasActiveDropdown: boolean
  setHasActiveDropdown: (active: boolean) => void
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined)

export function SidebarContextProvider({ children }: { children: React.ReactNode }) {
  const [hasActiveDropdown, setHasActiveDropdown] = useState(false)

  return (
    <SidebarContext.Provider value={{ hasActiveDropdown, setHasActiveDropdown }}>
      {children}
    </SidebarContext.Provider>
  )
}

export function useSidebarContext() {
  const context = useContext(SidebarContext)
  if (context === undefined) {
    throw new Error("useSidebarContext must be used within a SidebarContextProvider")
  }
  return context
}
