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
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts"

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

  const renderDashboard = () => (
    <>
      <Card className="bg-card border-border mb-6">
        <CardHeader>
          <CardTitle className="text-card-foreground">Server Control Board</CardTitle>
          <CardDescription>Monitor and control your database servers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(serverStates).map(([server, state]) => (
              <div key={server} className="p-4 border border-border rounded-lg bg-muted/20">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        state.status === "online"
                          ? "bg-green-500"
                          : state.status === "offline"
                            ? "bg-red-500"
                            : "bg-orange-500 animate-pulse"
                      }`}
                    ></div>
                    <h3 className="font-semibold text-card-foreground capitalize">{server}</h3>
                  </div>
                  <Badge
                    variant={
                      state.status === "online" ? "default" : state.status === "offline" ? "destructive" : "secondary"
                    }
                  >
                    {state.status}
                  </Badge>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">CPU:</span>
                    <span className="text-card-foreground">{state.cpu}%</span>
                  </div>
                  <Progress value={state.cpu} className="h-1" />

                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Memory:</span>
                    <span className="text-card-foreground">{state.memory}%</span>
                  </div>
                  <Progress value={state.memory} className="h-1" />

                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Uptime:</span>
                    <span className="text-card-foreground">{state.uptime}</span>
                  </div>
                </div>

                <div className="flex flex-col space-y-2">
                  <div className="flex space-x-1">
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1 h-8 text-xs bg-transparent"
                      onClick={() => handleServerAction(server, "start")}
                      disabled={state.status === "online"}
                    >
                      <Play className="h-3 w-3 mr-1" />
                      Start
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1 h-8 text-xs bg-transparent"
                      onClick={() => handleServerAction(server, "stop")}
                      disabled={state.status === "offline"}
                    >
                      <Square className="h-3 w-3 mr-1" />
                      Stop
                    </Button>
                  </div>
                  <Button
                    size="sm"
                    variant="secondary"
                    className="w-full h-8 text-xs"
                    onClick={() => handleServerAction(server, "restart")}
                    disabled={state.status === "offline"}
                  >
                    <RotateCcw className="h-3 w-3 mr-1" />
                    Restart
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">MySQL</p>
                <p className="text-2xl font-bold text-card-foreground">Active</p>
                <p className="text-xs text-muted-foreground">45 connections</p>
              </div>
              <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <Database className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-4">
              <Progress value={45} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">PostgreSQL</p>
                <p className="text-2xl font-bold text-card-foreground">Active</p>
                <p className="text-xs text-muted-foreground">32 connections</p>
              </div>
              <div className="h-12 w-12 rounded-lg bg-indigo-100 flex items-center justify-center">
                <Server className="h-6 w-6 text-indigo-600" />
              </div>
            </div>
            <div className="mt-4">
              <Progress value={32} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">MongoDB</p>
                <p className="text-2xl font-bold text-card-foreground">Active</p>
                <p className="text-xs text-muted-foreground">28 connections</p>
              </div>
              <div className="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center">
                <Activity className="h-6 w-6 text-green-600" />
              </div>
            </div>
            <div className="mt-4">
              <Progress value={28} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Redis</p>
                <p className="text-2xl font-bold text-card-foreground">Active</p>
                <p className="text-xs text-muted-foreground">15 connections</p>
              </div>
              <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center">
                <Zap className="h-6 w-6 text-orange-600" />
              </div>
            </div>
            <div className="mt-4">
              <Progress value={15} className="h-2" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-card-foreground">Performance Comparison</CardTitle>
            <CardDescription>Queries per second over time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="mysql"
                    stackId="1"
                    stroke="hsl(var(--chart-1))"
                    fill="hsl(var(--chart-1))"
                    fillOpacity={0.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="postgresql"
                    stackId="1"
                    stroke="hsl(var(--chart-2))"
                    fill="hsl(var(--chart-2))"
                    fillOpacity={0.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="mongodb"
                    stackId="1"
                    stroke="hsl(var(--chart-3))"
                    fill="hsl(var(--chart-3))"
                    fillOpacity={0.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="redis"
                    stackId="1"
                    stroke="hsl(var(--chart-4))"
                    fill="hsl(var(--chart-4))"
                    fillOpacity={0.6}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-card-foreground">Connection Status</CardTitle>
            <CardDescription>Current connections vs maximum capacity</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {connectionData.map((db) => (
                <div key={db.name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: db.color }}></div>
                    <span className="text-sm font-medium text-card-foreground">{db.name}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-muted-foreground">
                      {db.connections}/{db.maxConnections}
                    </span>
                    <Progress value={(db.connections / db.maxConnections) * 100} className="w-20 h-2" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground">Recent Query Executions</CardTitle>
          <CardDescription>Latest database operations across all systems</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                  MySQL
                </Badge>
                <code className="text-sm">SELECT * FROM users WHERE active = 1</code>
              </div>
              <div className="text-sm text-muted-foreground">2.3ms</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Badge variant="secondary" className="bg-indigo-100 text-indigo-700">
                  PostgreSQL
                </Badge>
                <code className="text-sm">CREATE INDEX idx_user_email ON users(email)</code>
              </div>
              <div className="text-sm text-muted-foreground">45.2ms</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Badge variant="secondary" className="bg-green-100 text-green-700">
                  MongoDB
                </Badge>
                <code className="text-sm">db.products.find({`{ category: "electronics" }`})</code>
              </div>
              <div className="text-sm text-muted-foreground">8.7ms</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Badge variant="secondary" className="bg-orange-100 text-orange-700">
                  Redis
                </Badge>
                <code className="text-sm">GET user:session:12345</code>
              </div>
              <div className="text-sm text-muted-foreground">0.8ms</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  )

  const renderQueryExecutor = () => (
    <div className="space-y-6">
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground">Query Executor</CardTitle>
          <CardDescription>Execute queries against different database systems</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-card-foreground">Database:</label>
              <select
                value={selectedDBMS}
                onChange={(e) => setSelectedDBMS(e.target.value)}
                className="px-3 py-2 border border-border rounded-md bg-input text-foreground"
              >
                <option value="mysql">MySQL</option>
                <option value="postgresql">PostgreSQL</option>
                <option value="mongodb">MongoDB</option>
                <option value="redis">Redis</option>
              </select>
            </div>
            <Textarea
              placeholder="Enter your query here..."
              className="min-h-[200px] font-mono text-sm bg-input border-border"
            />
            <div className="flex items-center space-x-2">
              <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                <Play className="h-4 w-4 mr-2" />
                Execute Query
              </Button>
              <Button variant="outline" className="border-border bg-transparent">
                <RefreshCw className="h-4 w-4 mr-2" />
                Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground">Query Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-muted/50 p-4 rounded-lg">
            <p className="text-sm text-muted-foreground">Execute a query to see results here...</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderPerformanceMonitor = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-card-foreground">Real-time Performance</CardTitle>
            <CardDescription>Queries per second across all databases</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[350px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" />
                  <YAxis stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="mysql"
                    stroke="hsl(var(--chart-1))"
                    fill="hsl(var(--chart-1))"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="postgresql"
                    stroke="hsl(var(--chart-2))"
                    fill="hsl(var(--chart-2))"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="mongodb"
                    stroke="hsl(var(--chart-3))"
                    fill="hsl(var(--chart-3))"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="redis"
                    stroke="hsl(var(--chart-4))"
                    fill="hsl(var(--chart-4))"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center justify-center space-x-6 mt-4">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-[hsl(var(--chart-1))]"></div>
                <span className="text-sm text-muted-foreground">MySQL</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-[hsl(var(--chart-2))]"></div>
                <span className="text-sm text-muted-foreground">PostgreSQL</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-[hsl(var(--chart-3))]"></div>
                <span className="text-sm text-muted-foreground">MongoDB</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-[hsl(var(--chart-4))]"></div>
                <span className="text-sm text-muted-foreground">Redis</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-card-foreground">Database Health Status</CardTitle>
            <CardDescription>Current performance metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-card-foreground">MySQL</span>
                  <span className="text-sm text-muted-foreground">220 QPS</span>
                </div>
                <Progress value={88} className="h-2" />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>CPU: 45%</span>
                  <span>Memory: 62%</span>
                  <span>Connections: 45/100</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-card-foreground">PostgreSQL</span>
                  <span className="text-sm text-muted-foreground">200 QPS</span>
                </div>
                <Progress value={80} className="h-2" />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>CPU: 38%</span>
                  <span>Memory: 58%</span>
                  <span>Connections: 32/100</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-card-foreground">MongoDB</span>
                  <span className="text-sm text-muted-foreground">175 QPS</span>
                </div>
                <Progress value={70} className="h-2" />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>CPU: 32%</span>
                  <span>Memory: 48%</span>
                  <span>Connections: 28/100</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-card-foreground">Redis</span>
                  <span className="text-sm text-muted-foreground">350 QPS</span>
                </div>
                <Progress value={95} className="h-2" />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>CPU: 15%</span>
                  <span>Memory: 25%</span>
                  <span>Connections: 15/100</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground">Performance Alerts</CardTitle>
          <CardDescription>Recent performance issues and notifications</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center space-x-3 p-3 bg-orange-50 border border-orange-200 rounded-lg">
              <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-orange-800">High CPU usage detected</p>
                <p className="text-xs text-orange-600">MySQL server CPU usage exceeded 80% for 5 minutes</p>
              </div>
              <span className="text-xs text-orange-600">2 min ago</span>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-green-800">Performance optimization completed</p>
                <p className="text-xs text-green-600">PostgreSQL index optimization improved query speed by 25%</p>
              </div>
              <span className="text-xs text-green-600">15 min ago</span>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-blue-800">Redis cache hit rate optimal</p>
                <p className="text-xs text-blue-600">Cache hit rate maintained above 95% for the last hour</p>
              </div>
              <span className="text-xs text-blue-600">1 hour ago</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderServerControl = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-card-foreground">Server Status Overview</CardTitle>
            <CardDescription>Real-time status of all database servers</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(serverStates).map(([server, state]) => (
                <div key={server} className="flex items-center justify-between p-3 border border-border rounded-lg">
                  <div className="flex items-center space-x-3">
                    {state.status === "online" ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : state.status === "offline" ? (
                      <XCircle className="h-5 w-5 text-red-500" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-orange-500" />
                    )}
                    <div>
                      <h3 className="font-medium text-card-foreground capitalize">{server}</h3>
                      <p className="text-sm text-muted-foreground">
                        CPU: {state.cpu}% | Memory: {state.memory}% | Uptime: {state.uptime}
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant={
                      state.status === "online" ? "default" : state.status === "offline" ? "destructive" : "secondary"
                    }
                  >
                    {state.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-card-foreground">Quick Actions</CardTitle>
            <CardDescription>Perform bulk operations on servers</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
                <Power className="h-4 w-4 mr-2" />
                Start All Servers
              </Button>
              <Button variant="outline" className="w-full border-border bg-transparent">
                <RotateCcw className="h-4 w-4 mr-2" />
                Restart All Servers
              </Button>
              <Button variant="destructive" className="w-full">
                <Square className="h-4 w-4 mr-2" />
                Stop All Servers
              </Button>
              <div className="pt-4 border-t border-border">
                <h4 className="font-medium text-card-foreground mb-2">System Information</h4>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <div className="flex justify-between">
                    <span>Total Servers:</span>
                    <span>4</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Online:</span>
                    <span className="text-green-600">
                      {Object.values(serverStates).filter((s) => s.status === "online").length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Offline:</span>
                    <span className="text-red-600">
                      {Object.values(serverStates).filter((s) => s.status === "offline").length}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground">Server Logs</CardTitle>
          <CardDescription>Recent server activities and events</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            <div className="flex items-start space-x-3 p-3 bg-muted/50 rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-card-foreground">MySQL server started successfully</p>
                <p className="text-xs text-muted-foreground">Server is now accepting connections on port 3306</p>
                <span className="text-xs text-muted-foreground">2 minutes ago</span>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3 bg-muted/50 rounded-lg">
              <div className="w-2 h-2 bg-orange-500 rounded-full mt-2"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-card-foreground">PostgreSQL high memory usage detected</p>
                <p className="text-xs text-muted-foreground">Memory usage reached 85%, consider optimization</p>
                <span className="text-xs text-muted-foreground">5 minutes ago</span>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3 bg-muted/50 rounded-lg">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-card-foreground">MongoDB index rebuild completed</p>
                <p className="text-xs text-muted-foreground">Performance optimization finished successfully</p>
                <span className="text-xs text-muted-foreground">10 minutes ago</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

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
          <h1 className="text-2xl font-bold text-sidebar-foreground">DBMS Lab</h1>
          <p className="text-sm text-muted-foreground">Database Experiment Platform</p>
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
                ? "Database Overview"
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
          {activeSection === "dashboard" && renderDashboard()}
          {activeSection === "server-control" && renderServerControl()}
          {activeSection === "query-executor" && renderQueryExecutor()}
          {activeSection === "performance" && renderPerformanceMonitor()}
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
