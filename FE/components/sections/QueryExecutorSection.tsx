import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Progress } from "@/components/ui/progress"
import { Play, RefreshCw } from "lucide-react"
import type { DBKey } from "@/lib/types"

type Props = {
  selectedDBMS: DBKey
  onChangeSelectedDBMS: (db: DBKey) => void
}

export default function QueryExecutorSection({ selectedDBMS, onChangeSelectedDBMS }: Props) {
  return (
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
                onChange={(e) => onChangeSelectedDBMS(e.target.value as DBKey)}
                className="px-3 py-2 border border-border rounded-md bg-input text-foreground"
              >
                <option value="mysql">MySQL</option>
                <option value="postgresql">PostgreSQL</option>
                <option value="mongodb">MongoDB</option>
                <option value="redis">Redis</option>
              </select>
            </div>
            <Textarea placeholder="Enter your query here..." className="min-h-[200px] font-mono text-sm bg-input border-border" />
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
}
