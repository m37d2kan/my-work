# Nikkei Futures Dashboard

## 概要
kabu ステーション API（auカブコム証券）を使用した日経先物リアルタイムダッシュボード。

## Architecture
- Backend: Node.js + Express (port 3001)
- Frontend: React + Vite (port 5173)
- kabu REST API: http://localhost:18080/kabusapi
- kabu WebSocket: ws://localhost:18081/kabusapi/websocket

## 起動手順
1. kabu ステーションを起動・ログイン
2. `cd backend && npm install && npm start`
3. `cd frontend && npm install && npm run dev`
4. ブラウザで http://localhost:5173 を開く

## Tech Stack
- Backend: Express, ws, axios, dotenv
- Frontend: React 18, Vite, recharts

## kabu Station API エンドポイント
| メソッド | パス | 説明 |
|---------|------|------|
| POST | /token | 認証トークン取得 |
| GET | /board/{symbol}@{exchange} | 板情報取得 |
| GET | /positions | 残高照会 |
| GET | /orders | 注文照会 |
| POST | /sendorder | 注文発注 |
| PUT | /cancelorder | 注文取消 |
| POST | /register | シンボル登録（プッシュ通知） |
| DELETE | /register | シンボル登録解除 |

## デフォルトシンボル
- Symbol: 169（日経225先物mini ※コントラクト月で変わる）
- Exchange: 2（OSE）
- SecurityType: 103（mini先物）

## 注文フィールド
- Side: "1"=売り, "2"=買い
- FrontOrderType: 1=指値, 2=成行
- CashMargin: 1=現物
- AccountType: 4=特定口座
- ExpireDay: 0=当日
