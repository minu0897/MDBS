"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { FileText, Download, RefreshCw, Loader2 } from "lucide-react"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000"

type LogFile = {
  filename: string
  size: number
  modified: number
  path: string
}

export default function LogViewerSection() {
  const [logFiles, setLogFiles] = useState<LogFile[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [downloadingFile, setDownloadingFile] = useState<string | null>(null)

  const loadLogFiles = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/logs/list`)
      const result = await response.json()

      if (result.ok && Array.isArray(result.data)) {
        setLogFiles(result.data)
      } else {
        throw new Error(result.error || "Failed to load log files")
      }
    } catch (error) {
      console.error("Failed to load log files:", error)
      alert(`로그 파일 조회 실패: ${error}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = async (filename: string) => {
    setDownloadingFile(filename)
    try {
      const response = await fetch(`${API_BASE}/logs/download/${filename}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Blob으로 변환
      const blob = await response.blob()

      // 다운로드 링크 생성
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()

      // 정리
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error("Download failed:", error)
      alert(`다운로드 실패: ${error}`)
    } finally {
      setDownloadingFile(null)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (timestamp: number): string => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  useEffect(() => {
    loadLogFiles()
  }, [])

  return (
    <div className="space-y-6">
      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-card-foreground">Log Files</CardTitle>
              <CardDescription>View and download RDG log files from the server</CardDescription>
            </div>
            <Button
              onClick={loadLogFiles}
              disabled={isLoading}
              variant="outline"
              className="border-border"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {logFiles.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">File Name</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Location</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Size</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Modified</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {logFiles.map((file) => (
                    <tr key={`${file.path}/${file.filename}`} className="border-b border-border hover:bg-muted/50">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm font-medium text-card-foreground">{file.filename}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-xs text-muted-foreground font-mono">
                          {file.path.includes('temp_log') ? 'temp_log/' : 'scripts/'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="secondary" className="font-mono text-xs bg-blue-100 text-blue-700 border-blue-300">
                          {formatFileSize(file.size)}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-sm text-muted-foreground">
                        {formatDate(file.modified)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          onClick={() => handleDownload(file.filename)}
                          disabled={downloadingFile === file.filename}
                          size="sm"
                          className="bg-primary text-primary-foreground hover:bg-primary/90"
                        >
                          {downloadingFile === file.filename ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Downloading...
                            </>
                          ) : (
                            <>
                              <Download className="h-4 w-4 mr-2" />
                              Download
                            </>
                          )}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-muted/50 p-8 rounded-lg text-center">
              <FileText className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-20" />
              <p className="text-sm text-muted-foreground">
                {isLoading ? "Loading log files..." : "No log files found. Click Refresh to check again."}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
