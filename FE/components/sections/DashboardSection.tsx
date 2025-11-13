import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Database, Server, Activity, Zap, Play, Square, RotateCcw, TrendingUp, Clock, CheckCircle2, XCircle, Send } from "lucide-react"
import { ResponsiveContainer, AreaChart, CartesianGrid, XAxis, YAxis, Tooltip, Area } from "recharts"
import type { ConnectionItem, PerformancePoint, ServerStates, DBKey } from "@/lib/types"

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

  // 시간 포맷 헬퍼 함수
  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    if (hours > 0) return `${hours}h ${minutes}m ${secs}s`
    if (minutes > 0) return `${minutes}m ${secs}s`
    return `${secs}s`
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
          <CardTitle className="text-card-foreground">Server Control Board</CardTitle>
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
                <CardTitle className="text-card-foreground">RDG Statistics</CardTitle>
                <CardDescription>Random Data Generator Performance Metrics</CardDescription>
              </div>
              {rdgRunning && (
                <Badge variant="default" className="bg-green-500">
                  <Activity className="h-3 w-3 mr-1 animate-pulse" />
                  Running
                </Badge>
              )}
              {!rdgRunning && rdgStats && (
                <Badge variant="secondary">Stopped</Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {rdgStats ? (
              <div className="space-y-4">
                {/* 주요 메트릭 그리드 */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-blue-50 dark:bg-blue-950/20 rounded-lg p-3 border border-blue-200 dark:border-blue-900">
                    <div className="flex items-center gap-2 mb-1">
                      <Send className="h-4 w-4 text-blue-600" />
                      <span className="text-xs text-muted-foreground">Total Sent</span>
                    </div>
                    <p className="text-2xl font-bold text-blue-600">{rdgStats.sent.toLocaleString()}</p>
                  </div>

                  <div className="bg-green-50 dark:bg-green-950/20 rounded-lg p-3 border border-green-200 dark:border-green-900">
                    <div className="flex items-center gap-2 mb-1">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      <span className="text-xs text-muted-foreground">Success</span>
                    </div>
                    <p className="text-2xl font-bold text-green-600">{rdgStats.ok.toLocaleString()}</p>
                  </div>

                  <div className="bg-red-50 dark:bg-red-950/20 rounded-lg p-3 border border-red-200 dark:border-red-900">
                    <div className="flex items-center gap-2 mb-1">
                      <XCircle className="h-4 w-4 text-red-600" />
                      <span className="text-xs text-muted-foreground">Failed</span>
                    </div>
                    <p className="text-2xl font-bold text-red-600">{rdgStats.fail.toLocaleString()}</p>
                  </div>

                  <div className="bg-purple-50 dark:bg-purple-950/20 rounded-lg p-3 border border-purple-200 dark:border-purple-900">
                    <div className="flex items-center gap-2 mb-1">
                      <TrendingUp className="h-4 w-4 text-purple-600" />
                      <span className="text-xs text-muted-foreground">Actual RPS</span>
                    </div>
                    <p className="text-2xl font-bold text-purple-600">{rdgStats.actual_rps.toFixed(2)}</p>
                  </div>
                </div>

                {/* 상세 정보 */}
                <div className="space-y-2 pt-2 border-t">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">Uptime</span>
                    </div>
                    <span className="font-medium">{formatUptime(rdgStats.uptime_sec)}</span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Success Rate</span>
                    <div className="flex items-center gap-2">
                      <Progress value={rdgStats.success_rate} className="w-20 h-2" />
                      <span className="font-medium">{rdgStats.success_rate.toFixed(2)}%</span>
                    </div>
                  </div>

                  {rdgStats.avg_latency_ms > 0 && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Avg Latency</span>
                      <span className="font-medium">{rdgStats.avg_latency_ms.toFixed(2)}ms</span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="h-[260px] flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <Activity className="h-12 w-12 mx-auto mb-3 opacity-20" />
                  <p>No RDG data available</p>
                  <p className="text-sm">Start RDG to see statistics</p>
                </div>
              </div>
            )}
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
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: db.color }} />
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

      {/* Recent Query Executions */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground">Recent Query Executions</CardTitle>
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
    </div>
  )
}
