import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { ResponsiveContainer, AreaChart, CartesianGrid, XAxis, YAxis, Tooltip, Area } from "recharts"
import type { PerformancePoint } from "@/lib/types"

type Props = {
  performanceData: PerformancePoint[]
}

export default function PerformanceMonitorSection({ performanceData }: Props) {
  return (
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
                  <Area type="monotone" dataKey="mysql" stroke="hsl(var(--chart-1))" fill="hsl(var(--chart-1))" fillOpacity={0.3} strokeWidth={2} />
                  <Area type="monotone" dataKey="postgresql" stroke="hsl(var(--chart-2))" fill="hsl(var(--chart-2))" fillOpacity={0.3} strokeWidth={2} />
                  <Area type="monotone" dataKey="mongodb" stroke="hsl(var(--chart-3))" fill="hsl(var(--chart-3))" fillOpacity={0.3} strokeWidth={2} />
                  <Area type="monotone" dataKey="redis" stroke="hsl(var(--chart-4))" fill="hsl(var(--chart-4))" fillOpacity={0.3} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center justify-center space-x-6 mt-4">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-[hsl(var(--chart-1))]" />
                <span className="text-sm text-muted-foreground">MySQL</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-[hsl(var(--chart-2))]" />
                <span className="text-sm text-muted-foreground">PostgreSQL</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-[hsl(var(--chart-3))]" />
                <span className="text-sm text-muted-foreground">MongoDB</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-[hsl(var(--chart-4))]" />
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
              {/* 예시 고정 값 - 원본 유지 */}
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
              <div className="w-2 h-2 bg-orange-500 rounded-full" />
              <div className="flex-1">
                <p className="text-sm font-medium text-orange-800">High CPU usage detected</p>
                <p className="text-xs text-orange-600">MySQL server CPU usage exceeded 80% for 5 minutes</p>
              </div>
              <span className="text-xs text-orange-600">2 min ago</span>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <div className="flex-1">
                <p className="text-sm font-medium text-green-800">Performance optimization completed</p>
                <p className="text-xs text-green-600">PostgreSQL index optimization improved query speed by 25%</p>
              </div>
              <span className="text-xs text-green-600">15 min ago</span>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="w-2 h-2 bg-blue-500 rounded-full" />
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
}
