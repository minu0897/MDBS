"use client"

import { useState, useEffect } from "react"
import {
  Database,
  Play,
  BarChart3,
  Monitor,
  Settings,
  Activity,
  Zap,
  Server,
  Bell,
  Menu,
  ChevronLeft,
  Download,
  RefreshCw,
  Terminal,
  Power,
  Square,
  RotateCcw,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"

import DashboardSection from "@/components/sections/DashboardSection"
import ServerControlSection from "@/components/sections/ServerControlSection"
import QueryExecutorSection from "@/components/sections/QueryExecutorSection"
import PerformanceMonitorSection from "@/components/sections/PerformanceMonitorSection"

//import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts"

export default function Dashboard() {
  const [activeSection, setActiveSection] = useState("dashboard")
  const [isMobile, setIsMobile] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [selectedDBMS, setSelectedDBMS] = useState("mysql")

  const [serverStates, setServerStates] = useState({
    mysql: { status: "online", cpu: 45, memory: 62, uptime: "2d 14h 32m" },
    postgresql: { status: "online", cpu: 38, memory: 58, uptime: "1d 8h 15m" },
    mongodb: { status: "online", cpu: 32, memory: 48, uptime: "3d 2h 45m" },
    redis: { status: "online", cpu: 15, memory: 25, uptime: "5d 12h 8m" },
  })

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768)
    }

    handleResize()
    window.addEventListener("resize", handleResize)

    return () => {
      window.removeEventListener("resize", handleResize)
    }
  }, [])

  const handleServerAction = (server: string, action: "start" | "stop" | "restart") => {
    setServerStates((prev) => ({
      ...prev,
      [server]: {
        ...prev[server as keyof typeof prev],
        status: action === "stop" ? "offline" : action === "restart" ? "restarting" : "online",
      },
    }))

    // 시뮬레이션: 재시작 후 온라인 상태로 변경
    if (action === "restart") {
      setTimeout(() => {
        setServerStates((prev) => ({
          ...prev,
          [server]: { ...prev[server as keyof typeof prev], status: "online" },
        }))
      }, 3000)
    }
  }

  const performanceData = [
    { name: "00:00", mysql: 120, postgresql: 110, mongodb: 95, redis: 200 },
    { name: "04:00", mysql: 135, postgresql: 125, mongodb: 105, redis: 220 },
    { name: "08:00", mysql: 180, postgresql: 165, mongodb: 140, redis: 280 },
    { name: "12:00", mysql: 220, postgresql: 200, mongodb: 175, redis: 350 },
    { name: "16:00", mysql: 195, postgresql: 185, mongodb: 160, redis: 320 },
    { name: "20:00", mysql: 150, postgresql: 140, mongodb: 120, redis: 250 },
  ]

  const connectionData = [
    { name: "MySQL", connections: 45, maxConnections: 100, color: "hsl(var(--chart-1))" },
    { name: "PostgreSQL", connections: 32, maxConnections: 100, color: "hsl(var(--chart-2))" },
    { name: "MongoDB", connections: 28, maxConnections: 100, color: "hsl(var(--chart-3))" },
    { name: "Redis", connections: 15, maxConnections: 100, color: "hsl(var(--chart-4))" },
  ]

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile Sidebar Toggle */}
      {isMobile && (
        <Button
          variant="outline"
          size="icon"
          className="fixed bottom-4 right-4 z-50 rounded-full h-12 w-12 shadow-lg bg-card border-border"
          onClick={() => setSidebarOpen(true)}
        >
          <Menu className="h-6 w-6" />
        </Button>
      )}

      <div
        className={`${isMobile ? "fixed inset-0 z-50 transform transition-transform duration-300 ease-in-out" : "w-64"} ${isMobile && !sidebarOpen ? "-translate-x-full" : "translate-x-0"} bg-sidebar border-r border-sidebar-border flex flex-col`}
      >
        {isMobile && (
          <div className="flex justify-end p-4">
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)}>
              <ChevronLeft className="h-6 w-6" />
            </Button>
          </div>
        )}
        <div className="p-6 border-b border-sidebar-border">
          <h1 className="text-2xl font-bold text-sidebar-foreground">MDBS Lab</h1>
          <p className="text-sm text-muted-foreground">Multiple Database Banking Simulation</p>
        </div>
        <div className="flex-1 py-4 overflow-y-auto">
          <nav className="space-y-1 px-2">
            <button
              onClick={() => setActiveSection("dashboard")}
              className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-r-md transition-colors ${activeSection === "dashboard" ? "text-sidebar-accent-foreground bg-sidebar-accent border-l-4 border-sidebar-accent" : "text-sidebar-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"}`}
            >
              <BarChart3 className="mr-3 h-5 w-5" />
              Dashboard
            </button>
            <button
              onClick={() => setActiveSection("server-control")}
              className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-r-md transition-colors ${activeSection === "server-control" ? "text-sidebar-accent-foreground bg-sidebar-accent border-l-4 border-sidebar-accent" : "text-sidebar-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"}`}
            >
              <Server className="mr-3 h-5 w-5" />
              Server Control
            </button>
            <button
              onClick={() => setActiveSection("query-executor")}
              className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-r-md transition-colors ${activeSection === "query-executor" ? "text-sidebar-accent-foreground bg-sidebar-accent border-l-4 border-sidebar-accent" : "text-sidebar-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"}`}
            >
              <Terminal className="mr-3 h-5 w-5" />
              Query Executor
            </button>
            <button
              onClick={() => setActiveSection("performance")}
              className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-r-md transition-colors ${activeSection === "performance" ? "text-sidebar-accent-foreground bg-sidebar-accent border-l-4 border-sidebar-accent" : "text-sidebar-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"}`}
            >
              <Monitor className="mr-3 h-5 w-5" />
              Performance Monitor
            </button>
            <button
              onClick={() => setActiveSection("connections")}
              className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-r-md transition-colors ${activeSection === "connections" ? "text-sidebar-accent-foreground bg-sidebar-accent border-l-4 border-sidebar-accent" : "text-sidebar-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"}`}
            >
              <Database className="mr-3 h-5 w-5" />
              Connections
            </button>
            <button
              onClick={() => setActiveSection("settings")}
              className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-r-md transition-colors ${activeSection === "settings" ? "text-sidebar-accent-foreground bg-sidebar-accent border-l-4 border-sidebar-accent" : "text-sidebar-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"}`}
            >
              <Settings className="mr-3 h-5 w-5" />
              Settings
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-card border-b border-border flex items-center justify-between px-4 py-4 md:px-6">
          <div className="flex items-center">
            {isMobile && (
              <Button variant="ghost" size="icon" className="mr-2" onClick={() => setSidebarOpen(true)}>
                <Menu className="h-5 w-5" />
              </Button>
            )}
            <h1 className="text-xl font-semibold text-card-foreground">
              {activeSection === "dashboard"
                ? "Dashboard"
                : activeSection === "server-control"
                  ? "Server Control"
                  : activeSection === "query-executor"
                    ? "Query Executor"
                    : activeSection === "performance"
                      ? "Performance Monitor"
                      : activeSection === "connections"
                        ? "Connection Manager"
                        : "Settings"}
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="outline" className="border-border bg-transparent">
              <Download className="h-4 w-4 mr-2" />
              Export Data
            </Button>

            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              <span className="absolute top-0 right-0 h-2 w-2 bg-destructive rounded-full"></span>
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src="/placeholder.svg?height=32&width=32" alt="User" />
                    <AvatarFallback>DV</AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="bg-popover border-border">
                <DropdownMenuItem>Profile</DropdownMenuItem>
                <DropdownMenuItem>Settings</DropdownMenuItem>
                <DropdownMenuItem>Logout</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
        {activeSection === "dashboard" && (
          <DashboardSection
            serverStates={serverStates}
            onServerAction={handleServerAction}
            performanceData={performanceData}
            connectionData={connectionData}
          />
        )}
        {activeSection === "server-control" && (
          <ServerControlSection serverStates={serverStates} />
        )}
        {activeSection === "query-executor" && (
          <QueryExecutorSection
            selectedDBMS={selectedDBMS}
            onChangeSelectedDBMS={setSelectedDBMS}
          />
        )}
        {activeSection === "performance" && (
          <PerformanceMonitorSection performanceData={performanceData} />
        )}
          {activeSection !== "dashboard" &&
            activeSection !== "server-control" &&
            activeSection !== "query-executor" &&
            activeSection !== "performance" && (
              <div className="flex items-center justify-center h-full">
                <Card className="w-full max-w-md bg-card border-border">
                  <CardHeader>
                    <CardTitle className="text-card-foreground">Coming Soon</CardTitle>
                    <CardDescription>This section is under development and will be available soon.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-card-foreground">
                      The{" "}
                      {activeSection === "performance"
                        ? "Performance Monitor"
                        : activeSection === "connections"
                          ? "Connection Manager"
                          : "Settings"}{" "}
                      module is currently being built. Please check back later.
                    </p>
                  </CardContent>
                </Card>
              </div>
            )}
        </main>
      </div>
    </div>
  )
}
