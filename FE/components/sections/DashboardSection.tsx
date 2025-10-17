import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Database, Server, Activity, Zap, Play, Square, RotateCcw } from "lucide-react"
import { ResponsiveContainer, AreaChart, CartesianGrid, XAxis, YAxis, Tooltip, Area } from "recharts"
import type { ConnectionItem, PerformancePoint, ServerStates, DBKey } from "@/lib/types"

type Props = {
  serverStates: ServerStates
  onServerAction: (server: DBKey, action: "start" | "stop" | "restart") => void
  performanceData: PerformancePoint[]
  connectionData: ConnectionItem[]
}

export default function DashboardSection({
  serverStates,
  onServerAction,
  performanceData,
  connectionData,
}: Props) {

  return (
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
                <p className="text-sm font-medium text-muted-foreground">Oracle</p>
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

      {/* Chart + Connection Status */}
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
                  <Area type="monotone" dataKey="mysql" stackId="1" stroke="hsl(var(--chart-1))" fill="hsl(var(--chart-1))" fillOpacity={0.6} />
                  <Area type="monotone" dataKey="postgresql" stackId="1" stroke="hsl(var(--chart-2))" fill="hsl(var(--chart-2))" fillOpacity={0.6} />
                  <Area type="monotone" dataKey="mongodb" stackId="1" stroke="hsl(var(--chart-3))" fill="hsl(var(--chart-3))" fillOpacity={0.6} />
                  <Area type="monotone" dataKey="oracle" stackId="1" stroke="hsl(var(--chart-4))" fill="hsl(var(--chart-4))" fillOpacity={0.6} />
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
  )
}
