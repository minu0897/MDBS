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
  type?: "debit" | "credit"  // 출금(-) 또는 입금(+)
}

type AccountBalance = {
  account_id: number
  name: string
  balance: number
}

type BankBalance = {
  bank: string
  total_amount: number
}

export default function DataExplorerSection() {
  const [activeFeature, setActiveFeature] = useState<FeatureType>("transfer-history")

  // Transfer History Search State
  const [selectedDbms, setSelectedDbms] = useState("")
  const [searchValue, setSearchValue] = useState("")
  const [searchResults, setSearchResults] = useState<TransferHistory[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [accountBalance, setAccountBalance] = useState<AccountBalance | null>(null)

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
    { id: "transfer" as FeatureType, label: "Execute Transfer", icon: ArrowRightLeft },
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
      // Name으로만 검색 (account 제거)
      const queryId = "query.ledger_entries.by_name"
      const params = { name: searchValue }

      let response

      // MongoDB는 별도 엔드포인트 사용
      if (selectedDbms === "mongo") {
        response = await fetch(`${API_BASE}/db/file/mongo`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            collection: "ledger_entries",
            id: queryId,
            params: params
          })
        })
      } else {
        response = await fetch(`${API_BASE}/db/file/sql`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            dbms: selectedDbms,
            id: queryId,
            params: params
          })
        })
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()

      if (result.ok && Array.isArray(result.data)) {
        // LEDGER_ENTRIES를 TransferHistory 형태로 변환
        const transformed = result.data.map((entry: any, index: number) => {
          const rawAmount = entry.AMOUNT || entry.amount || 0
          return {
            id: entry.ENTRY_ID || entry.entry_id || index,
            sender_bank: selectedDbms.toUpperCase(),
            sender_account: entry.ACCOUNT_ID || entry.account_id || "N/A",
            receiver_bank: "-",
            receiver_account: "-",
            amount: Math.abs(rawAmount),
            timestamp: entry.CREATED_AT || entry.created_at || "",
            type: rawAmount < 0 ? "debit" as const : "credit" as const
          }
        })
        setSearchResults(transformed)
      } else {
        setSearchResults([])
      }

      // Account balance는 더 이상 조회하지 않음
      setAccountBalance(null)
    } catch (error) {
      console.error("Search failed:", error)
      alert(`조회 실패: ${error}`)
      setSearchResults([])
      setAccountBalance(null)
    } finally {
      setIsSearching(false)
    }
  }

  const fetchAccountBalance = async (dbms: string, accountId: number) => {
    try {
      let response

      if (dbms === "mongo") {
        response = await fetch(`${API_BASE}/db/file/mongo`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            collection: "accounts",
            id: "query.accounts.by_account_id",
            params: { account_id: accountId.toString() }
          })
        })
      } else {
        response = await fetch(`${API_BASE}/db/file/sql`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            dbms: dbms,
            id: "query.accounts.by_account_id",
            params: { account_id: accountId }
          })
        })
      }

      const result = await response.json()

      if (result.ok && Array.isArray(result.data) && result.data.length > 0) {
        const account = result.data[0]
        setAccountBalance({
          account_id: account.ACCOUNT_ID || account.account_id || account._id,
          name: account.NAME || account.name || "N/A",
          balance: parseFloat(account.BALANCE || account.balance || 0)
        })
      } else {
        setAccountBalance(null)
      }
    } catch (error) {
      console.error("Failed to fetch account balance:", error)
      setAccountBalance(null)
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
      const srcAccountId = parseInt(senderAccount)
      const dstAccountId = parseInt(receiverAccount)
      const dstBank = Math.floor(dstAccountId / 100000).toString()

      // RDG와 동일한 UUID 생성 방식: {src}->{dst}-{uuid}
      const srcPrefix = senderBank.substring(0, 2)
      const dstPrefix = receiverBank.substring(0, 2)
      const uuid = crypto.randomUUID()
      const idempotencyKey = `${srcPrefix}->${dstPrefix}-${uuid}`

      // 내부 이체 (같은 DBMS)
      if (senderBank === receiverBank) {
        await executeInternalTransfer(senderBank, srcAccountId, dstAccountId, dstBank, amount, idempotencyKey)
      } else {
        // 외부 이체 (다른 DBMS)
        await executeExternalTransfer(senderBank, receiverBank, srcAccountId, dstAccountId, dstBank, amount, idempotencyKey)
      }

      alert(`✅ 이체 완료!\n송금: ${senderBank}(${senderAccount})\n수취: ${receiverBank}(${receiverAccount})\n금액: ₩${amount.toLocaleString()}`)
      setSenderAccount("")
      setReceiverAccount("")
      setTransferAmount("")
    } catch (error) {
      console.error("Transfer failed:", error)
      alert(`❌ 이체 실패: ${error}`)
    } finally {
      setIsTransferring(false)
    }
  }

  // 내부 이체 처리 (RDG와 동일한 로직)
  const executeInternalTransfer = async (
    dbms: string,
    srcAccountId: number,
    dstAccountId: number,
    dstBank: string,
    amount: number,
    idempotencyKey: string
  ) => {
    // Step 1: 송금 보류
    const holdResult = await callProcedure(dbms, "remittance/hold", {
      src_account_id: srcAccountId,
      dst_account_id: dstAccountId,
      dst_bank: dstBank,
      amount: amount.toString(),
      idempotency_key: idempotencyKey,
      type: "1"
    }, ["sp_remittance_hold", [srcAccountId, dstAccountId, dstBank, amount, idempotencyKey, "1"], 2, ["txn_id", "status"]])

    if (!holdResult || holdResult.status !== "1") {
      // 타임아웃(null) 시 hold 해제 시도
      if (!holdResult) {
        await releaseHold(dbms, idempotencyKey)
      }
      throw new Error(`송금 보류 실패: ${holdResult?.status || 'Unknown'}`)
    }

    // Step 2: 이체 확정
    const confirmResult = await callProcedure(dbms, "transfer/confirm/internal", {
      idempotency_key: idempotencyKey
    }, ["sp_transfer_confirm_internal", [idempotencyKey], 2, ["status", "result"]])

    if (!confirmResult || confirmResult.status !== "2") {
      // 확정 실패 시 hold 해제
      await releaseHold(dbms, idempotencyKey)
      throw new Error(`이체 확정 실패: ${confirmResult?.status || 'Unknown'}`)
    }
  }

  // 외부 이체 처리 (RDG와 동일한 로직)
  const executeExternalTransfer = async (
    srcDbms: string,
    dstDbms: string,
    srcAccountId: number,
    dstAccountId: number,
    dstBank: string,
    amount: number,
    idempotencyKey: string
  ) => {
    // Step 1: 송금 보류 (송금측 DBMS)
    const holdResult = await callProcedure(srcDbms, "remittance/hold", {
      src_account_id: srcAccountId,
      dst_account_id: dstAccountId,
      dst_bank: dstBank,
      amount: amount.toString(),
      idempotency_key: idempotencyKey,
      type: "2"
    }, ["sp_remittance_hold", [srcAccountId, dstAccountId, dstBank, amount, idempotencyKey, "2"], 2, ["txn_id", "status"]])

    if (!holdResult || holdResult.status !== "1") {
      // 타임아웃(null) 시 hold 해제 시도
      if (!holdResult) {
        await releaseHold(srcDbms, idempotencyKey)
      }
      throw new Error(`송금 보류 실패: ${holdResult?.status || 'Unknown'}`)
    }

    // Step 2: 수금 준비 (수취측 DBMS)
    const prepareResult = await callProcedure(dstDbms, "receive/prepare", {
      src_account_id: srcAccountId,
      dst_account_id: dstAccountId,
      dst_bank: dstBank,
      amount: amount.toString(),
      idempotency_key: idempotencyKey,
      type: "3"
    }, ["sp_receive_prepare", [srcAccountId, dstAccountId, dstBank, amount, idempotencyKey, "3"], 2, ["txn_id", "status"]])

    if (!prepareResult || prepareResult.status !== "1") {
      await releaseHold(srcDbms, idempotencyKey)
      throw new Error(`수금 준비 실패: ${prepareResult?.status || 'Unknown'}`)
    }

    // Step 3: 출금 확정 (송금측 DBMS)
    const debitResult = await callProcedure(srcDbms, "confirm/debit/local", {
      idempotency_key: idempotencyKey
    }, ["sp_confirm_debit_local", [idempotencyKey], 3, ["txn_id", "status", "result"]])

    if (!debitResult || debitResult.status !== "2") {
      await releaseHold(srcDbms, idempotencyKey)
      throw new Error(`출금 확정 실패: ${debitResult?.status || 'Unknown'}`)
    }

    // Step 4: 입금 확정 (수취측 DBMS)
    const creditResult = await callProcedure(dstDbms, "confirm/credit/local", {
      idempotency_key: idempotencyKey
    }, ["sp_confirm_credit_local", [idempotencyKey], 3, ["txn_id", "status", "result"]])

    if (!creditResult || creditResult.status !== "2") {
      // 입금 실패 시에는 hold 해제하지 않음 (이미 출금 완료되었으므로)
      throw new Error(`입금 확정 실패: ${creditResult?.status || 'Unknown'}`)
    }
  }

  // 프로시저 호출 헬퍼 (MongoDB vs SQL)
  const callProcedure = async (
    dbms: string,
    mongoPath: string,
    mongoPayload: any,
    sqlParams: [string, any[], number, string[]]
  ) => {
    if (dbms === "mongo") {
      const response = await fetch(`${API_BASE}/mongo_proc/${mongoPath}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(mongoPayload)
      })
      const result = await response.json()
      if (!result.ok) throw new Error(result.error || "MongoDB procedure failed")
      return result.data
    } else {
      const [procName, args, outCount, outNames] = sqlParams
      const payload: any = {
        dbms: dbms,
        name: procName,
        args: args,
        out_count: outCount,
        out_names: outNames
      }

      if (dbms === "postgres") {
        payload.mode = "func"
      }

      if (dbms === "oracle") {
        // Oracle OUT 타입 지정
        const outTypes = procName === "sp_remittance_hold" || procName === "sp_receive_prepare"
          ? ["NUMBER", "VARCHAR2"]
          : procName === "sp_transfer_confirm_internal" || procName === "sp_remittance_release"
          ? ["VARCHAR2", "VARCHAR2"]
          : ["NUMBER", "VARCHAR2", "VARCHAR2"]
        payload.out_types = outTypes
        payload.args = [...args, ...Array(outCount).fill(null)]
      }

      const response = await fetch(`${API_BASE}/db/proc/exec`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
      const result = await response.json()
      if (!result.ok) throw new Error(result.error || "SQL procedure failed")
      return result.data
    }
  }

  // Hold 해제
  const releaseHold = async (dbms: string, idempotencyKey: string) => {
    try {
      await callProcedure(dbms, "remittance/release", {
        idempotency_key: idempotencyKey
      }, ["sp_remittance_release", [idempotencyKey], 2, ["status", "result"]])
    } catch (error) {
      console.error("Hold 해제 실패:", error)
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
              <CardDescription>Search transfer records by DBMS and account name</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                      Account Name
                    </label>
                    <Input
                      placeholder="Enter account name..."
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

          {/* 계좌 잔액 표시 */}
          {accountBalance && (
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-card-foreground">Account Balance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                  <div>
                    <div className="text-sm text-muted-foreground">Account ID</div>
                    <div className="text-lg font-semibold text-card-foreground">{accountBalance.account_id}</div>
                    <div className="text-sm text-muted-foreground mt-1">{accountBalance.name}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-muted-foreground">Current Balance</div>
                    <div className="text-2xl font-bold text-card-foreground">₩{accountBalance.balance.toLocaleString()}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

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
                        <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Type</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Account</th>
                        <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Amount</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Timestamp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {searchResults.map((record) => (
                        <tr key={record.id} className="border-b border-border hover:bg-muted/50">
                          <td className="py-3 px-4 text-sm text-card-foreground">{record.id}</td>
                          <td className="py-3 px-4">
                            {record.type === "debit" ? (
                              <Badge variant="destructive" className="bg-red-500">출금</Badge>
                            ) : (
                              <Badge variant="default" className="bg-green-500">입금</Badge>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <div className="text-sm">
                              <Badge variant="secondary" className="mb-1">{record.sender_bank}</Badge>
                              <div className="text-muted-foreground">{record.sender_account}</div>
                            </div>
                          </td>
                          <td className={`py-3 px-4 text-right text-sm font-medium ${record.type === "debit" ? "text-red-500" : "text-green-500"}`}>
                            {record.type === "debit" ? "-" : "+"}₩{record.amount.toLocaleString()}
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
