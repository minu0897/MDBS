import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Checkbox } from "@/components/ui/checkbox"
import { Database, Server, Activity, Zap, Play, Square, RotateCcw, TrendingUp, Clock, CheckCircle2, XCircle, Send, Trash2, AlertTriangle } from "lucide-react"
import { ResponsiveContainer, AreaChart, CartesianGrid, XAxis, YAxis, Tooltip, Area } from "recharts"
import type { ConnectionItem, PerformancePoint, ServerStates, DBKey } from "@/lib/types"
import { useState } from "react"

type RDGStats = {
  uptime_sec: number
  sent: number
  ok: number
  fail: number
  success_rate: number
  actual_rps: number
  avg_latency_ms: number
  in_flight: number
}

type Props = {
  serverStates: ServerStates
  onServerAction: (server: DBKey, action: "start" | "stop" | "restart") => void
  performanceData: PerformancePoint[]
  connectionData: ConnectionItem[]
  isLoading?: boolean
  rdgStats?: RDGStats | null
  rdgRunning?: boolean
}

export default function DashboardSection({
  serverStates,
  onServerAction,
  performanceData,
  connectionData,
  isLoading = false,
  rdgStats = null,
  rdgRunning = false,
}: Props) {
  const [resetPassword, setResetPassword] = useState("")
  const [showPasswordInput, setShowPasswordInput] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [resetResult, setResetResult] = useState<{ success: boolean; message: string } | null>(null)

  // RDG Control States
  const [rdgPassword, setRdgPassword] = useState("")
  const [showRdgDialog, setShowRdgDialog] = useState(false)
  const [rdgAction, setRdgAction] = useState<"start" | "stop" | null>(null)
  const [rdgProcessing, setRdgProcessing] = useState(false)
  const [rdgResult, setRdgResult] = useState<{ success: boolean; message: string } | null>(null)

  // RDG Config States
  const [rdgConfig, setRdgConfig] = useState({
    rps: 7,
    concurrent: 10,
    min_amount: 1000,
    max_amount: 100000,
    allow_same_db: true,
    active_dbms: ["mysql", "postgres", "oracle"] as string[]
  })

  // 시간 포맷 헬퍼 함수
  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    if (hours > 0) return `${hours}h ${minutes}m ${secs}s`
    if (minutes > 0) return `${minutes}m ${secs}s`
    return `${secs}s`
  }

  // 환경 리셋 핸들러
  const handleResetEnvironment = async () => {
    if (!resetPassword) {
      setResetResult({ success: false, message: "Password is required" })
      return
    }

    setResetting(true)
    setResetResult(null)

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
      const response = await fetch(`${API_BASE}/system/reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: resetPassword }),
      })

      const data = await response.json()

      if (response.ok && data.data?.success) {
        setResetResult({ success: true, message: data.data.message })
        setShowPasswordInput(false)
        setResetPassword("")
      } else {
        setResetResult({
          success: false,
          message: data.message || data.data?.message || "Reset failed",
        })
      }
    } catch (error) {
      setResetResult({
        success: false,
        message: error instanceof Error ? error.message : "Network error",
      })
    } finally {
      setResetting(false)
    }
  }

  // DBMS 체크박스 핸들러
  const handleDbmsToggle = (dbms: string) => {
    setRdgConfig(prev => ({
      ...prev,
      active_dbms: prev.active_dbms.includes(dbms)
        ? prev.active_dbms.filter(d => d !== dbms)
        : [...prev.active_dbms, dbms]
    }))
  }

  // RDG 컨트롤 핸들러
  const handleRdgControl = async () => {
    if (!rdgPassword) {
      setRdgResult({ success: false, message: "Password is required" })
      return
    }

    if (rdgAction === "start" && rdgConfig.active_dbms.length === 0) {
      setRdgResult({ success: false, message: "At least one DBMS must be selected" })
      return
    }

    setRdgProcessing(true)
    setRdgResult(null)

    try {
      // RDG는 무조건 서버에서 실행 (DOCKER_API_BASE 사용)
      const API_BASE = process.env.NEXT_PUBLIC_DOCKER_API_URL || "http://localhost:5000"

      // Start 시에는 설정 포함, Stop 시에는 password만
      const payload = rdgAction === "start"
        ? { ...rdgConfig, password: rdgPassword }
        : { password: rdgPassword }

      const response = await fetch(`${API_BASE}/rdg/${rdgAction}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      const data = await response.json()

      if (response.ok && data.ok) {
        setRdgResult({
          success: true,
          message: `RDG ${rdgAction === "start" ? "started" : "stopped"} successfully`
        })
        setShowRdgDialog(false)
        setRdgPassword("")
        setRdgAction(null)
        // Refresh page after 1 second to update RDG status
        setTimeout(() => window.location.reload(), 1000)
      } else {
        setRdgResult({
          success: false,
          message: data.error || `Failed to ${rdgAction} RDG`,
        })
      }
    } catch (error) {
      setRdgResult({
        success: false,
        message: error instanceof Error ? error.message : "Network error",
      })
    } finally {
      setRdgProcessing(false)
    }
  }


  return (
    <div className="relative">
      {/* Loading Indicator */}
      {isLoading && (
        <div className="absolute top-4 right-4 z-50">
          <div className="flex items-center gap-2 bg-card border border-border rounded-lg px-3 py-2 shadow-lg">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-primary"></div>
            <span className="text-sm text-muted-foreground">조회 중</span>
          </div>
        </div>
      )}

      {/* Main Content */}
      <>
      {/* Server Control Board */}
      <Card className="bg-card border-border mb-6">
        <CardHeader>
          <CardTitle className="text-card-foreground">Server Control Board(조회만 구현)</CardTitle>
          <CardDescription>Monitor and control your database servers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {(Object.entries(serverStates) as Array<[DBKey, ServerStates[DBKey]]>).map(([server, state]) => (
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
                    />
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
                      onClick={() => onServerAction(server, "start")}
                      disabled={state.status === "online"}
                    >
                      <Play className="h-3 w-3 mr-1" />
                      Start
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1 h-8 text-xs bg-transparent"
                      onClick={() => onServerAction(server, "stop")}
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
                    onClick={() => onServerAction(server, "restart")}
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

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {connectionData.map((db, index) => {
          const icons = [Database, Server, Activity, Zap]
          const bgColors = ["bg-blue-100", "bg-indigo-100", "bg-green-100", "bg-orange-100"]
          const iconColors = ["text-blue-600", "text-indigo-600", "text-green-600", "text-orange-600"]
          const Icon = icons[index] || Database

          return (
            <Card key={db.name} className="bg-card border-border">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground capitalize">{db.name}</p>
                    <p className="text-2xl font-bold text-card-foreground">Active</p>
                    <p className="text-xs text-muted-foreground">{db.connections} connections</p>
                  </div>
                  <div className={`h-12 w-12 rounded-lg ${bgColors[index]} flex items-center justify-center`}>
                    <Icon className={`h-6 w-6 ${iconColors[index]}`} />
                  </div>
                </div>
                <div className="mt-4">
                  <Progress value={(db.connections / db.maxConnections) * 100} className="h-2" />
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Chart + Connection Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card className="bg-card border-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-card-foreground flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  RDG Controller
                </CardTitle>
                <CardDescription>Random Data Generator Control & Statistics</CardDescription>
              </div>
              {rdgRunning && (
                <Badge variant="default" className="bg-green-500">
                  <Activity className="h-3 w-3 mr-1 animate-pulse" />
                  Running
                </Badge>
              )}
              {!rdgRunning && (
                <Badge variant="secondary">Stopped</Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* RDG 통계 (Running일 때만 표시) */}
              {rdgRunning && rdgStats && (
                <div className="space-y-3 p-3 bg-muted/50 rounded-lg">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground">Total Sent</p>
                      <p className="text-lg font-bold text-blue-600">{rdgStats.sent.toLocaleString()}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground">Success</p>
                      <p className="text-lg font-bold text-green-600">{rdgStats.ok.toLocaleString()}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground">Failed</p>
                      <p className="text-lg font-bold text-red-600">{rdgStats.fail.toLocaleString()}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground">Actual RPS</p>
                      <p className="text-lg font-bold text-purple-600">{rdgStats.actual_rps.toFixed(2)}</p>
                    </div>
                  </div>
                  <div className="text-sm text-center text-muted-foreground pt-2 border-t">
                    Uptime: {formatUptime(rdgStats.uptime_sec)} | Success Rate: {rdgStats.success_rate.toFixed(2)}%
                  </div>
                </div>
              )}

              {/* Control Buttons */}
              <div className="space-y-2">
                {!rdgRunning ? (
                  <Button
                    variant="default"
                    className="w-full bg-green-600 hover:bg-green-700"
                    onClick={() => {
                      setRdgAction("start")
                      setShowRdgDialog(true)
                      setRdgResult(null)
                    }}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Start RDG
                  </Button>
                ) : (
                  <Button
                    variant="destructive"
                    className="w-full"
                    onClick={() => {
                      setRdgAction("stop")
                      setShowRdgDialog(true)
                      setRdgResult(null)
                    }}
                  >
                    <Square className="h-4 w-4 mr-2" />
                    Stop RDG
                  </Button>
                )}
              </div>

              {/* Result Message */}
              {rdgResult && (
                <div
                  className={`p-3 rounded-lg border ${
                    rdgResult.success
                      ? "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900"
                      : "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900"
                  }`}
                >
                  <p
                    className={`text-sm font-medium ${
                      rdgResult.success ? "text-green-900 dark:text-green-200" : "text-red-900 dark:text-red-200"
                    }`}
                  >
                    {rdgResult.message}
                  </p>
                </div>
              )}

              {/* Info */}
              <div className="text-xs text-muted-foreground space-y-1 pt-2 border-t">
                <p>• RDG generates random transactions across all DBMS</p>
                <p>• Change password via RDG_PASSWORD environment variable</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-card-foreground flex items-center gap-2">
              <Trash2 className="h-5 w-5" />
              Reset Environment
            </CardTitle>
            <CardDescription>Clear all transaction data and reset account balances</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Warning Message */}
              <div className="flex items-start gap-2 p-3 bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-900 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-orange-900 dark:text-orange-200">
                  <p className="font-semibold mb-1">Warning: This action cannot be undone</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Deletes all transaction data (MySQL, PostgreSQL, Oracle, MongoDB)</li>
                    <li>Resets all account balances to initial state</li>
                    <li>Resets auto-increment sequences</li>
                    <li>Cannot be performed while RDG is running</li>
                  </ul>
                </div>
              </div>

              {/* RDG Running Warning */}
              {rdgRunning && (
                <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  <p className="text-sm text-red-900 dark:text-red-200 font-medium">
                    RDG is currently running. Stop RDG before resetting.
                  </p>
                </div>
              )}

              {/* Password Input (shown when button clicked) */}
              {showPasswordInput && !rdgRunning && (
                <div className="space-y-3">
                  <div>
                    <label className="text-sm font-medium text-card-foreground block mb-2">
                      Enter Password to Confirm
                    </label>
                    <input
                      type="password"
                      value={resetPassword}
                      onChange={(e) => setResetPassword(e.target.value)}
                      placeholder="Enter reset password"
                      className="w-full px-3 py-2 border border-border rounded-md bg-background text-card-foreground"
                      disabled={resetting}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleResetEnvironment()
                      }}
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="destructive"
                      className="flex-1"
                      onClick={handleResetEnvironment}
                      disabled={resetting || !resetPassword}
                    >
                      {resetting ? "Resetting..." : "Confirm Reset"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowPasswordInput(false)
                        setResetPassword("")
                        setResetResult(null)
                      }}
                      disabled={resetting}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}

              {/* Reset Button (shown when password input hidden) */}
              {!showPasswordInput && !rdgRunning && (
                <Button
                  variant="destructive"
                  className="w-full"
                  onClick={() => setShowPasswordInput(true)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Reset Environment
                </Button>
              )}

              {/* Result Message */}
              {resetResult && (
                <div
                  className={`p-3 rounded-lg border ${
                    resetResult.success
                      ? "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900"
                      : "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900"
                  }`}
                >
                  <p
                    className={`text-sm font-medium ${
                      resetResult.success ? "text-green-900 dark:text-green-200" : "text-red-900 dark:text-red-200"
                    }`}
                  >
                    {resetResult.message}
                  </p>
                </div>
              )}

              {/* Info */}
              <div className="text-xs text-muted-foreground space-y-1 pt-2 border-t">
                <p>• After reset: Each DB's accounts (n00001~n00005) will have ₩100,000,000 balance</p>
                <p>• Total initial balance: ₩2,000,000,000 (₩100,000,000 × 5 accounts × 4 DBMS)</p>
                <p>• Change password via RESET_PASSWORD environment variable</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Query Executions */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground">Recent Query Executions(구현x)</CardTitle>
          <CardDescription>Latest database operations across all systems</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Badge variant="secondary" className="bg-blue-100 text-blue-700">MySQL</Badge>
                <code className="text-sm">SELECT * FROM users WHERE active = 1</code>
              </div>
              <div className="text-sm text-muted-foreground">2.3ms</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Badge variant="secondary" className="bg-indigo-100 text-indigo-700">PostgreSQL</Badge>
                <code className="text-sm">CREATE INDEX idx_user_email ON users(email)</code>
              </div>
              <div className="text-sm text-muted-foreground">45.2ms</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Badge variant="secondary" className="bg-green-100 text-green-700">MongoDB</Badge>
                <code className="text-sm">db.products.find({`{ category: "electronics" }`})</code>
              </div>
              <div className="text-sm text-muted-foreground">8.7ms</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Badge variant="secondary" className="bg-orange-100 text-orange-700">Oracle</Badge>
                <code className="text-sm">SELECT * FROM accounts WHERE balance &gt; 1000</code>
              </div>
              <div className="text-sm text-muted-foreground">3.2ms</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </>

    {/* RDG Config Dialog */}
    <Dialog open={showRdgDialog} onOpenChange={setShowRdgDialog}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{rdgAction === "start" ? "Start RDG" : "Stop RDG"}</DialogTitle>
          <DialogDescription>
            {rdgAction === "start"
              ? "Configure RDG settings and enter password to start"
              : "Enter password to stop RDG"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* RDG Configuration (Start only) */}
          {rdgAction === "start" && (
            <>
              {/* Active DBMS */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Active DBMS</label>
                <div className="grid grid-cols-2 gap-2">
                  {["mysql", "postgres", "oracle", "mongo"].map((dbms) => (
                    <div key={dbms} className="flex items-center space-x-2">
                      <Checkbox
                        id={dbms}
                        checked={rdgConfig.active_dbms.includes(dbms)}
                        onCheckedChange={() => handleDbmsToggle(dbms)}
                      />
                      <label
                        htmlFor={dbms}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 capitalize cursor-pointer"
                      >
                        {dbms}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* RPS */}
              <div className="space-y-2">
                <label htmlFor="rps" className="text-sm font-medium">
                  RPS (Requests Per Second)
                </label>
                <input
                  id="rps"
                  type="number"
                  value={rdgConfig.rps}
                  onChange={(e) => setRdgConfig({...rdgConfig, rps: parseInt(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background text-card-foreground"
                  min="1"
                  max="1000"
                />
              </div>

              {/* Concurrent */}
              <div className="space-y-2">
                <label htmlFor="concurrent" className="text-sm font-medium">
                  Concurrent Limit
                </label>
                <input
                  id="concurrent"
                  type="number"
                  value={rdgConfig.concurrent}
                  onChange={(e) => setRdgConfig({...rdgConfig, concurrent: parseInt(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background text-card-foreground"
                  min="1"
                  max="1000"
                />
              </div>

              {/* Amount Range */}
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-2">
                  <label htmlFor="min_amount" className="text-sm font-medium">
                    Min Amount
                  </label>
                  <input
                    id="min_amount"
                    type="number"
                    value={rdgConfig.min_amount}
                    onChange={(e) => setRdgConfig({...rdgConfig, min_amount: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-border rounded-md bg-background text-card-foreground"
                    min="0"
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="max_amount" className="text-sm font-medium">
                    Max Amount
                  </label>
                  <input
                    id="max_amount"
                    type="number"
                    value={rdgConfig.max_amount}
                    onChange={(e) => setRdgConfig({...rdgConfig, max_amount: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-border rounded-md bg-background text-card-foreground"
                    min="0"
                  />
                </div>
              </div>

              {/* Allow Same DB */}
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="allow_same_db"
                  checked={rdgConfig.allow_same_db}
                  onCheckedChange={(checked) => setRdgConfig({...rdgConfig, allow_same_db: checked as boolean})}
                />
                <label
                  htmlFor="allow_same_db"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                >
                  Allow Same DB Transfers
                </label>
              </div>
            </>
          )}

          {/* Password */}
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={rdgPassword}
              onChange={(e) => setRdgPassword(e.target.value)}
              placeholder="Enter RDG password"
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-card-foreground"
              disabled={rdgProcessing}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleRdgControl()
              }}
            />
          </div>

          {/* Result Message */}
          {rdgResult && (
            <div
              className={`p-3 rounded-lg border ${
                rdgResult.success
                  ? "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900"
                  : "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900"
              }`}
            >
              <p
                className={`text-sm font-medium ${
                  rdgResult.success ? "text-green-900 dark:text-green-200" : "text-red-900 dark:text-red-200"
                }`}
              >
                {rdgResult.message}
              </p>
            </div>
          )}
        </div>

        {/* Dialog Footer */}
        <div className="flex gap-2">
          <Button
            variant={rdgAction === "start" ? "default" : "destructive"}
            className="flex-1"
            onClick={handleRdgControl}
            disabled={rdgProcessing || !rdgPassword}
          >
            {rdgProcessing ? "Processing..." : `Confirm ${rdgAction === "start" ? "Start" : "Stop"}`}
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              setShowRdgDialog(false)
              setRdgPassword("")
              setRdgAction(null)
              setRdgResult(null)
            }}
            disabled={rdgProcessing}
          >
            Cancel
          </Button>
        </div>
      </DialogContent>
    </Dialog>
    </div>
  )
}
