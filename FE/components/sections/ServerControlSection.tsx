import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { CheckCircle, XCircle, AlertTriangle, Power, RotateCcw, Square } from "lucide-react"
import type { ServerStates } from "@/lib/types"

type Props = {
  serverStates: ServerStates
}

export default function ServerControlSection({ serverStates }: Props) {
  return (
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
                  <Badge variant={state.status === "online" ? "default" : state.status === "offline" ? "destructive" : "secondary"}>
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
              <div className="w-2 h-2 bg-green-500 rounded-full mt-2" />
              <div className="flex-1">
                <p className="text-sm font-medium text-card-foreground">MySQL server started successfully</p>
                <p className="text-xs text-muted-foreground">Server is now accepting connections on port 3306</p>
                <span className="text-xs text-muted-foreground">2 minutes ago</span>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3 bg-muted/50 rounded-lg">
              <div className="w-2 h-2 bg-orange-500 rounded-full mt-2" />
              <div className="flex-1">
                <p className="text-sm font-medium text-card-foreground">PostgreSQL high memory usage detected</p>
                <p className="text-xs text-muted-foreground">Memory usage reached 85%, consider optimization</p>
                <span className="text-xs text-muted-foreground">5 minutes ago</span>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3 bg-muted/50 rounded-lg">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2" />
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
}
