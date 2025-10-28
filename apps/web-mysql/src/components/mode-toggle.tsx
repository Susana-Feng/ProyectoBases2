import { Moon, Sun, Monitor } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useTheme } from "@/components/theme-provider"
import { useSidebarContext } from "@/contexts/sidebar-context"

interface ModeToggleProps {
  isExpanded?: boolean
}

export function ModeToggle({ isExpanded = false }: ModeToggleProps) {
  const { theme, setTheme } = useTheme()
  const { setHasActiveDropdown } = useSidebarContext()

  const getThemeIcon = () => {
    switch (theme) {
      case "light":
        return <Sun className="h-4 w-4" />
      case "dark":
        return <Moon className="h-4 w-4" />
      default:
        return <Monitor className="h-4 w-4" />
    }
  }

  const getThemeLabel = () => {
    switch (theme) {
      case "light":
        return "Claro"
      case "dark":
        return "Oscuro"
      default:
        return "Sistema"
    }
  }

  return (
    <DropdownMenu 
      onOpenChange={(open) => {
        setHasActiveDropdown(open)
      }}
    >
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          className={`${isExpanded ? 'w-full justify-start gap-2 px-2' : 'w-10 h-10 p-0'} text-neutral-700 dark:text-neutral-200 hover:bg-neutral-200 dark:hover:bg-neutral-700`}
          onMouseDown={(e) => {
            // Prevent the sidebar from detecting this as a mouse leave event
            e.stopPropagation()
          }}
        >
          {getThemeIcon()}
          {isExpanded && (
            <span className="text-sm">
              {getThemeLabel()}
            </span>
          )}
          <span className="sr-only">Cambiar tema</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={isExpanded ? "start" : "center"} className="w-40">
        <DropdownMenuItem onClick={() => setTheme("light")} className="gap-2">
          <Sun className="h-4 w-4" />
          Claro
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("dark")} className="gap-2">
          <Moon className="h-4 w-4" />
          Oscuro
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("system")} className="gap-2">
          <Monitor className="h-4 w-4" />
          Sistema
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
