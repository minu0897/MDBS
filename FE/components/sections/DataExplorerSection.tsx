"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Search, DollarSign, ArrowRightLeft, Database, User, Hash, Loader2 } from "lucide-react"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000"

type FeatureType = "transfer-history" | "total-balance" | "transfer"

type SearchCriteria = "account" | "name"

type TransferHistory = {
  id: number
  sender_bank: string
  sender_account: string
  receiver_bank: string
  receiver_account: string
  amount: number
  timestamp: string
}

type BankBalance = {
  bank: string
  total_amount: number
}

export default function DataExplorerSection() {
  const [activeFeature, setActiveFeature] = useState<FeatureType>("transfer-history")

  // Transfer History Search State
  const [selectedDbms, setSelectedDbms] = useState("")
  const [searchCriteria, setSearchCriteria] = useState<SearchCriteria>("account")
  const [searchValue, setSearchValue] = useState("")
  const [searchResults, setSearchResults] = useState<TransferHistory[]>([])
  const [isSearching, setIsSearching] = useState(false)

  // Total Balance State
  const [bankBalances, setBankBalances] = useState<BankBalance[]>([])
  const [isLoadingBalances, setIsLoadingBalances] = useState(false)

  // Transfer State
  const [senderBank, setSenderBank] = useState("mysql")
  const [senderAccount, setSenderAccount] = useState("")
  const [receiverBank, setReceiverBank] = useState("mysql")
  const [receiverAccount, setReceiverAccount] = useState("")
  const [transferAmount, setTransferAmount] = useState("")
  const [isTransferring, setIsTransferring] = useState(false)

  const features = [
    { id: "transfer-history" as FeatureType, label: "Transfer History", icon: Search },
    { id: "total-balance" as FeatureType, label: "Total Balance", icon: DollarSign },
    { id: "transfer" as FeatureType, label: "Execute Transfer(구현x)", icon: ArrowRightLeft },
  ]

  const banks = [
    { value: "mysql", label: "MySQL" },
    { value: "postgres", label: "PostgreSQL" },
    { value: "mongo", label: "MongoDB" },
    { value: "oracle", label: "Oracle" },
  ]

  const handleSearch = async () => {
    if (!selectedDbms) {
      alert("DBMS를 선택해주세요")
      return
    }

    setIsSearching(true)
    try {
      // SQL 파일 ID 결정
      const queryId = searchCriteria === "account"
        ? "query.ledger_entries.by_account_id"
        : "query.ledger_entries.by_name"

      // 파라미터 구성
      const params = searchCriteria === "account"
        ? { account_id: searchValue }
        : { name: searchValue }

      const response = await fetch(`${API_BASE}/db/file/sql`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dbms: selectedDbms,
          id: queryId,
          params: params
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()

      if (result.ok && Array.isArray(result.data)) {
        // LEDGER_ENTRIES를 TransferHistory 형태로 변환
        const transformed = result.data.map((entry: any, index: number) => ({
          id: entry.ENTRY_ID || entry.entry_id || index,
          sender_bank: selectedDbms.toUpperCase(),
          sender_account: entry.ACCOUNT_ID || entry.account_id || "N/A",
          receiver_bank: "-",
          receiver_account: "-",
          amount: Math.abs(entry.AMOUNT || entry.amount || 0),
          timestamp: entry.CREATED_AT || entry.created_at || ""
        }))
        setSearchResults(transformed)
      } else {
        setSearchResults([])
      }
    } catch (error) {
      console.error("Search failed:", error)
      alert(`조회 실패: ${error}`)
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  const handleLoadBalances = async () => {
    setIsLoadingBalances(true)
    try {
      const balances: BankBalance[] = []

      // 각 DBMS별로 총 잔액 조회
      for (const bank of banks) {
        try {
          let response

          // MongoDB는 /db/file/mongo 엔드포인트 사용
          if (bank.value === "mongo") {
            response = await fetch(`${API_BASE}/db/file/mongo`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                collection: "accounts",
                id: "query.accounts.all_balance",
                params: {}
              })
            })
          } else {
            response = await fetch(`${API_BASE}/db/file/sql`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                dbms: bank.value,
                id: "query.accounts.all_balance",
                params: {}
              })
            })
          }

          const result = await response.json()

          if (result.ok && Array.isArray(result.data) && result.data.length > 0) {
            // query.accounts.all_balance는 sum(balance) as balance를 반환
            const rawAmount = result.data[0].BALANCE || result.data[0].balance || 0
            const totalAmount = Math.floor(Number(rawAmount))  // 소수점 제거

            balances.push({
              bank: bank.label,
              total_amount: totalAmount
            })
          } else {
            balances.push({ bank: bank.label, total_amount: 0 })
          }
        } catch (error) {
          console.error(`Failed to load balance for ${bank.label}:`, error)
          balances.push({ bank: bank.label, total_amount: 0 })
        }
      }

      setBankBalances(balances)
    } catch (error) {
      console.error("Failed to load balances:", error)
      alert("잔액 조회 실패")
    } finally {
      setIsLoadingBalances(false)
    }
  }

  const handleTransfer = async () => {
    if (!senderAccount || !receiverAccount || !transferAmount) {
      alert("모든 필드를 입력해주세요")
      return
    }

    const amount = parseFloat(transferAmount)
    if (isNaN(amount) || amount <= 0) {
      alert("올바른 금액을 입력해주세요")
      return
    }

    setIsTransferring(true)
    try {
      // MongoDB 간 이체는 별도 엔드포인트 사용
      if (senderBank === "mongo" || receiverBank === "mongo") {
        const response = await fetch(`${API_BASE}/mongo/transfer`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            sender_account: senderAccount,
            receiver_account: receiverAccount,
            amount: amount,
            allow_same_db: senderBank === receiverBank
          })
        })

        const result = await response.json()
        if (result.ok) {
          alert(`이체 완료! TXN ID: ${result.data?.txn_id || 'N/A'}`)
        } else {
          throw new Error(result.error || "이체 실패")
        }
      } else {
        // RDB 간 이체 (MySQL, PostgreSQL, Oracle)
        // TODO: 사용할 stored procedure 이름 확인 필요
        // 예시: MDBS.sp_transfer 또는 transfer_between_accounts 등

        alert("RDB 간 이체 기능은 stored procedure 연동이 필요합니다.")
        // const response = await fetch(`${API_BASE}/db/proc/exec`, {
        //   method: "POST",
        //   headers: { "Content-Type": "application/json" },
        //   body: JSON.stringify({
        //     dbms: senderBank,
        //     name: "transfer_procedure_name",
        //     args: [senderAccount, receiverAccount, amount],
        //     out_count: 2,
        //     out_names: ["txn_id", "status"]
        //   })
        // })
      }

      setSenderAccount("")
      setReceiverAccount("")
      setTransferAmount("")
    } catch (error) {
      console.error("Transfer failed:", error)
      alert(`이체 실패: ${error}`)
    } finally {
      setIsTransferring(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Feature Selection Tabs */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground">Data Explorer</CardTitle>
          <CardDescription>Explore bank data, view balances, and execute transfers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {features.map((feature) => {
              const Icon = feature.icon
              return (
                <Button
                  key={feature.id}
                  onClick={() => setActiveFeature(feature.id)}
                  variant={activeFeature === feature.id ? "default" : "outline"}
                  className={
                    activeFeature === feature.id
                      ? "bg-primary text-primary-foreground"
                      : "border-border bg-transparent"
                  }
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {feature.label}
                </Button>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Transfer History Search */}
      {activeFeature === "transfer-history" && (
        <>
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-card-foreground">Transfer History Search</CardTitle>
              <CardDescription>Search transfer records by DBMS, account number, or name</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium text-card-foreground mb-2 block">
                      DBMS
                    </label>
                    <select
                      value={selectedDbms}
                      onChange={(e) => setSelectedDbms(e.target.value)}
                      className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground"
                    >
                      <option value="">Select DBMS</option>
                      {banks.map((bank) => (
                        <option key={bank.value} value={bank.value}>
                          {bank.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-card-foreground mb-2 block">
                      Search By
                    </label>
                    <select
                      value={searchCriteria}
                      onChange={(e) => setSearchCriteria(e.target.value as SearchCriteria)}
                      className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground"
                    >
                      <option value="account">Account Number</option>
                      <option value="name">Account Name</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-card-foreground mb-2 block">
                      Search Value
                    </label>
                    <Input
                      placeholder={`Enter ${searchCriteria === "account" ? "account number" : "name"}...`}
                      value={searchValue}
                      onChange={(e) => setSearchValue(e.target.value)}
                      className="bg-input border-border"
                    />
                  </div>
                </div>

                <Button
                  onClick={handleSearch}
                  disabled={isSearching || !selectedDbms || !searchValue}
                  className="bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  {isSearching ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Searching...
                    </>
                  ) : (
                    <>
                      <Search className="h-4 w-4 mr-2" />
                      Search
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-card-foreground">Search Results</CardTitle>
            </CardHeader>
            <CardContent>
              {searchResults.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">ID</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Sender</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Receiver</th>
                        <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Amount</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Timestamp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {searchResults.map((record) => (
                        <tr key={record.id} className="border-b border-border hover:bg-muted/50">
                          <td className="py-3 px-4 text-sm text-card-foreground">{record.id}</td>
                          <td className="py-3 px-4">
                            <div className="text-sm">
                              <Badge variant="secondary" className="mb-1">{record.sender_bank}</Badge>
                              <div className="text-muted-foreground">{record.sender_account}</div>
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <div className="text-sm">
                              <Badge variant="secondary" className="mb-1">{record.receiver_bank}</Badge>
                              <div className="text-muted-foreground">{record.receiver_account}</div>
                            </div>
                          </td>
                          <td className="py-3 px-4 text-right text-sm font-medium text-card-foreground">
                            ₩{record.amount.toLocaleString()}
                          </td>
                          <td className="py-3 px-4 text-sm text-muted-foreground">{record.timestamp}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="bg-muted/50 p-8 rounded-lg text-center">
                  <Search className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-20" />
                  <p className="text-sm text-muted-foreground">No results yet. Use the search form above to find transfer records.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Total Balance View */}
      {activeFeature === "total-balance" && (
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-card-foreground">Total Balance by Bank</CardTitle>
            <CardDescription>View total amount stored in each database</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Button
                onClick={handleLoadBalances}
                disabled={isLoadingBalances}
                className="bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {isLoadingBalances ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Loading...
                  </>
                ) : (
                  <>
                    <DollarSign className="h-4 w-4 mr-2" />
                    Load Total Balances
                  </>
                )}
              </Button>

              {bankBalances.length > 0 ? (
                <>
                  {/* Total Sum Card */}
                  <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20 rounded-lg p-6 border-2 border-purple-200 dark:border-purple-900 mb-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <DollarSign className="h-6 w-6 text-purple-600" />
                          <span className="text-lg font-semibold text-purple-900 dark:text-purple-100">Total Balance (All Banks)</span>
                        </div>
                        <p className="text-5xl font-bold text-purple-600">
                          ₩{bankBalances.reduce((sum, b) => sum + b.total_amount, 0).toLocaleString()}
                        </p>
                      </div>
                      <div className="text-right text-sm text-muted-foreground">
                        <p>{bankBalances.length} databases</p>
                      </div>
                    </div>
                  </div>

                  {/* Individual Bank Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {bankBalances.map((balance, index) => {
                      const colors = [
                        { bg: "bg-blue-50 dark:bg-blue-950/20", border: "border-blue-200 dark:border-blue-900", text: "text-blue-600" },
                        { bg: "bg-indigo-50 dark:bg-indigo-950/20", border: "border-indigo-200 dark:border-indigo-900", text: "text-indigo-600" },
                        { bg: "bg-green-50 dark:bg-green-950/20", border: "border-green-200 dark:border-green-900", text: "text-green-600" },
                        { bg: "bg-orange-50 dark:bg-orange-950/20", border: "border-orange-200 dark:border-orange-900", text: "text-orange-600" },
                      ]
                      const color = colors[index] || colors[0]

                      return (
                        <div
                          key={balance.bank}
                          className={`${color.bg} rounded-lg p-4 border ${color.border}`}
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <Database className={`h-5 w-5 ${color.text}`} />
                            <span className="text-sm font-medium text-muted-foreground">{balance.bank}</span>
                          </div>
                          <p className={`text-3xl font-bold ${color.text}`}>
                            ₩{balance.total_amount.toLocaleString()}
                          </p>
                        </div>
                      )
                    })}
                  </div>
                </>
              ) : (
                <div className="bg-muted/50 p-8 rounded-lg text-center">
                  <DollarSign className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-20" />
                  <p className="text-sm text-muted-foreground">Click the button above to load balance data</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Transfer Execution */}
      {activeFeature === "transfer" && (
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-card-foreground">Execute Transfer</CardTitle>
            <CardDescription>Transfer money between accounts across different databases</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Sender Info */}
              <div className="p-4 border border-border rounded-lg bg-muted/20">
                <h3 className="text-sm font-semibold text-card-foreground mb-4 flex items-center">
                  <User className="h-4 w-4 mr-2" />
                  Sender Information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-card-foreground mb-2 block">
                      Bank
                    </label>
                    <select
                      value={senderBank}
                      onChange={(e) => setSenderBank(e.target.value)}
                      className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground"
                    >
                      {banks.map((bank) => (
                        <option key={bank.value} value={bank.value}>
                          {bank.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-card-foreground mb-2 block">
                      Account Number
                    </label>
                    <Input
                      placeholder="Enter sender account..."
                      value={senderAccount}
                      onChange={(e) => setSenderAccount(e.target.value)}
                      className="bg-input border-border"
                    />
                  </div>
                </div>
              </div>

              {/* Transfer Arrow */}
              <div className="flex justify-center">
                <ArrowRightLeft className="h-6 w-6 text-muted-foreground" />
              </div>

              {/* Receiver Info */}
              <div className="p-4 border border-border rounded-lg bg-muted/20">
                <h3 className="text-sm font-semibold text-card-foreground mb-4 flex items-center">
                  <User className="h-4 w-4 mr-2" />
                  Receiver Information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-card-foreground mb-2 block">
                      Bank
                    </label>
                    <select
                      value={receiverBank}
                      onChange={(e) => setReceiverBank(e.target.value)}
                      className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground"
                    >
                      {banks.map((bank) => (
                        <option key={bank.value} value={bank.value}>
                          {bank.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-card-foreground mb-2 block">
                      Account Number
                    </label>
                    <Input
                      placeholder="Enter receiver account..."
                      value={receiverAccount}
                      onChange={(e) => setReceiverAccount(e.target.value)}
                      className="bg-input border-border"
                    />
                  </div>
                </div>
              </div>

              {/* Amount */}
              <div>
                <label className="text-sm font-medium text-card-foreground mb-2 block flex items-center">
                  <Hash className="h-4 w-4 mr-2" />
                  Transfer Amount (₩)
                </label>
                <Input
                  type="number"
                  placeholder="Enter amount..."
                  value={transferAmount}
                  onChange={(e) => setTransferAmount(e.target.value)}
                  className="bg-input border-border"
                />
              </div>

              {/* Submit Button */}
              <Button
                onClick={handleTransfer}
                disabled={isTransferring}
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {isTransferring ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing Transfer...
                  </>
                ) : (
                  <>
                    <ArrowRightLeft className="h-4 w-4 mr-2" />
                    Execute Transfer
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
