"use client"

import useSWR from "swr"
import { useMemo, useState, useEffect } from "react"
import {
  Database,
  BarChart3,
  Monitor,
  Settings,
  Server,
  Bell,
  Menu,
  ChevronLeft,
  Download,
  Terminal,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

import DashboardSection from "@/components/sections/DashboardSection"
import ServerControlSection from "@/components/sections/ServerControlSection"
import QueryExecutorSection from "@/components/sections/QueryExecutorSection"
import PerformanceMonitorSection from "@/components/sections/PerformanceMonitorSection"
import type { ServerStates, DockerStatsResponse, DBKey, ServerStatus } from "@/lib/types"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";


const fetcher = () =>
  fetch(`${API_BASE}/system/docker/stats`).then((r) => {
    if (!r.ok) throw new Error("Failed to fetch");
    return r.json();
  }).then((response) => {
    // API 응답이 { data: { containers: [...], ok: true } } 형태
    const data = response.data;
    return data;
  })

// Docker stats를 ServerStates로 변환하는 함수
function transformDockerStatsToServerStates(dockerStats: DockerStatsResponse | undefined): ServerStates {

  const defaultState: ServerStates = {
    mysql: { status: "offline", cpu: 0, memory: 0, uptime: "-" },
    postgresql: { status: "offline", cpu: 0, memory: 0, uptime: "-" },
    mongodb: { status: "offline", cpu: 0, memory: 0, uptime: "-" },
    oracle: { status: "offline", cpu: 0, memory: 0, uptime: "-" },
  }

  if (!dockerStats?.containers || !Array.isArray(dockerStats.containers)) {
    return defaultState
  }


  // 컨테이너 이름을 DBKey로 매핑 (postgres -> postgresql)
  const nameMap: Record<string, DBKey> = {
    mysql: "mysql",
    postgres: "postgresql",
    mongodb: "mongodb",
    mongo: "mongodb",
    oracle: "oracle",
  }

  dockerStats.containers.forEach((container) => {
    const containerName = container.name.toLowerCase()

    const dbKey = nameMap[containerName]

    if (dbKey) {
      // Docker state를 ServerStatus로 변환
      let status: ServerStatus = "offline"
      if (container.state.toLowerCase() === "running") {
        status = "online"
      } else if (container.state.toLowerCase().includes("restart")) {
        status = "restarting"
      }

      // uptime 계산 (임시로 state 기반)
      const uptime = container.state === "running" ? "Active" : "-"

      const transformed = {
        status,
        cpu: Math.round(container.cpu * 10) / 10,
        memory: Math.round(container.mem_perc * 10) / 10,
        uptime,
      }
      defaultState[dbKey] = transformed
    }
  })
  return defaultState
}

export default function Dashboard() {
  const [activeSection, setActiveSection] = useState("dashboard")
  const [isMobile, setIsMobile] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [selectedDBMS, setSelectedDBMS] = useState<DBKey>("mysql")

  // 1) SWR 폴링으로 서버 상태 주기 업데이트
  const { data, error, isValidating, mutate } = useSWR<DockerStatsResponse>("/api/servers", fetcher, {
    refreshInterval: 3000, // 3초마다 재검증
    revalidateOnFocus: false,
  })

  // 2) Docker stats를 ServerStates로 변환
  const serverStates = useMemo<ServerStates>(() => {
    const transformed = transformDockerStatsToServerStates(data)
    return transformed
  }, [data])

  // 3) 서버 액션 (start/stop/restart) - API 호출 후 재검증
  const handleServerAction = async (server: DBKey, action: "start" | "stop" | "restart") => {
    try {
      await fetch(`${API_BASE}/api/servers/${server}/actions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      })
      // 서버 액션 후 즉시 재검증
      await mutate()
    } catch (error) {
    }
  }

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    handleResize()
    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  const performanceData = [
    { name: "00:00", mysql: 120, postgresql: 110, mongodb: 95, oracle: 200 },
    { name: "04:00", mysql: 135, postgresql: 125, mongodb: 105, oracle: 220 },
    { name: "08:00", mysql: 180, postgresql: 165, mongodb: 140, oracle: 280 },
    { name: "12:00", mysql: 220, postgresql: 200, mongodb: 175, oracle: 350 },
    { name: "16:00", mysql: 195, postgresql: 185, mongodb: 160, oracle: 320 },
    { name: "20:00", mysql: 150, postgresql: 140, mongodb: 120, oracle: 250 },
  ]

  const connectionData = [
    { name: "MySQL", connections: 45, maxConnections: 100, color: "hsl(var(--chart-1))" },
    { name: "PostgreSQL", connections: 32, maxConnections: 100, color: "hsl(var(--chart-2))" },
    { name: "MongoDB", connections: 28, maxConnections: 100, color: "hsl(var(--chart-3))" },
    { name: "Oracle", connections: 15, maxConnections: 100, color: "hsl(var(--chart-4))" },
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
        className={`${
          isMobile
            ? "fixed inset-0 z-50 transform transition-transform duration-300 ease-in-out"
            : "w-64"
        } ${isMobile && !sidebarOpen ? "-translate-x-full" : "translate-x-0"} bg-sidebar border-r border-sidebar-border flex flex-col`}
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
              className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-r-md transition-colors ${
                activeSection === "dashboard"
                  ? "text-sidebar-accent-foreground bg-sidebar-accent border-l-4 border-sidebar-accent"
                  : "text-sidebar-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"
              }`}
            >
              <BarChart3 className="mr-3 h-5 w-5" />
              Dashboard
            </button>
            <button
              onClick={() => setActiveSection("server-control")}
              className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-r-md transition-colors ${
                activeSection === "server-control"
                  ? "text-sidebar-accent-foreground bg-sidebar-accent border-l-4 border-sidebar-accent"
                  : "text-sidebar-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"
              }`}
            >
              <Server className="mr-3 h-5 w-5" />
              Server Control
            </button>
            <button
              onClick={() => setActiveSection("query-executor")}
              className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-r-md transition-colors ${
                activeSection === "query-executor"
                  ? "text-sidebar-accent-foreground bg-sidebar-accent border-l-4 border-sidebar-accent"
                  : "text-sidebar-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"
              }`}
            >
              <Terminal className="mr-3 h-5 w-5" />
              Query Executor
            </button>
            <button
              onClick={() => setActiveSection("performance")}
              className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-r-md transition-colors ${
                activeSection === "performance"
                  ? "text-sidebar-accent-foreground bg-sidebar-accent border-l-4 border-sidebar-accent"
                  : "text-sidebar-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"
              }`}
            >
              <Monitor className="mr-3 h-5 w-5" />
              Performance Monitor
            </button>
            <button
              onClick={() => setActiveSection("connections")}
              className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-r-md transition-colors ${
                activeSection === "connections"
                  ? "text-sidebar-accent-foreground bg-sidebar-accent border-l-4 border-sidebar-accent"
                  : "text-sidebar-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"
              }`}
            >
              <Database className="mr-3 h-5 w-5" />
              Connections
            </button>
            <button
              onClick={() => setActiveSection("settings")}
              className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-r-md transition-colors ${
                activeSection === "settings"
                  ? "text-sidebar-accent-foreground bg-sidebar-accent border-l-4 border-sidebar-accent"
                  : "text-sidebar-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"
              }`}
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

        {/* 에러 상태 안내 */}
        {error && (
          <div className="px-4 md:px-6 py-2">
            <Card className="bg-destructive/10 border-destructive">
              <CardContent className="py-3 text-sm">
                서버 상태를 불러오지 못했습니다. BE의 `/api/servers` 응답을 확인해주세요.
              </CardContent>
            </Card>
          </div>
        )}

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
          {activeSection === "server-control" && <ServerControlSection serverStates={serverStates} />}
          {activeSection === "query-executor" && (
            <QueryExecutorSection selectedDBMS={selectedDBMS} onChangeSelectedDBMS={setSelectedDBMS} />
          )}
          {activeSection === "performance" && <PerformanceMonitorSection performanceData={performanceData} />}

          {activeSection !== "dashboard" &&
            activeSection !== "server-control" &&
            activeSection !== "query-executor" &&
            activeSection !== "performance" && (
              <div className="flex items-center justify-center h-full">
                <Card className="w-full max-w-md bg-card border-border">
                  <CardHeader>
                    <CardTitle className="text-card-foreground">Coming Soon</CardTitle>
                    <CardDescription>
                      This section is under development and will be available soon.
                    </CardDescription>
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
