import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from '@tanstack/react-router'
import { Toaster } from 'sonner'
import { ThemeProvider } from '@/components/theme-provider'
import './index.css'
import { router } from './router.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="system" storageKey="mssql-loader-theme">
      <RouterProvider router={router} />
      <Toaster />
    </ThemeProvider>
  </StrictMode>,
)
