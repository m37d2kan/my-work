import { fmtPrice } from '../utils/format';

const LEVELS = 5;

function buildLevels(data, prefix) {
  const levels = [];
  for (let i = 1; i <= LEVELS; i++) {
    const entry = data?.[`${prefix}${i}`];
    levels.push(entry ?? { Price: null, Qty: null });
  }
  return levels;
}

export default function OrderBook({ data }) {
  if (!data) {
    return (
      <div className="card order-book">
        <div className="card-title">板情報</div>
        <div className="loading">-</div>
      </div>
    );
  }

  const asks = buildLevels(data, 'Sell'); // Sell1..Sell5: best ask is Sell1
  const bids = buildLevels(data, 'Buy'); // Buy1..Buy5: best bid is Buy1

  const maxAskQty = Math.max(...asks.map((a) => a.Qty ?? 0), 1);
  const maxBidQty = Math.max(...bids.map((b) => b.Qty ?? 0), 1);

  return (
    <div className="card order-book">
      <div className="card-title">板情報</div>

      {/* 売気配 over */}
      <div className="ob-over">
        <span className="ob-label-over">OVER</span>
        <span className="ob-qty-over">{data.OverSellQty ?? '-'}</span>
      </div>

      {/* 売気配 (asks) — 逆順で表示: Sell5 → Sell1 */}
      <div className="ob-asks">
        {[...asks].reverse().map((ask, i) => (
          <div key={i} className="ob-row ask-row">
            <span className="ob-price ask-price">{fmtPrice(ask.Price)}</span>
            <div className="ob-bar-wrap">
              <div
                className="ob-bar ask-bar"
                style={{ width: `${((ask.Qty ?? 0) / maxAskQty) * 100}%` }}
              />
            </div>
            <span className="ob-qty">{ask.Qty ?? '-'}</span>
          </div>
        ))}
      </div>

      {/* 現在値 */}
      <div className="ob-mid">
        <span className="ob-mid-price">{fmtPrice(data.CurrentPrice)}</span>
      </div>

      {/* 買気配 (bids) — Buy1 → Buy5 */}
      <div className="ob-bids">
        {bids.map((bid, i) => (
          <div key={i} className="ob-row bid-row">
            <span className="ob-qty">{bid.Qty ?? '-'}</span>
            <div className="ob-bar-wrap">
              <div
                className="ob-bar bid-bar"
                style={{ width: `${((bid.Qty ?? 0) / maxBidQty) * 100}%` }}
              />
            </div>
            <span className="ob-price bid-price">{fmtPrice(bid.Price)}</span>
          </div>
        ))}
      </div>

      {/* 買気配 under */}
      <div className="ob-under">
        <span className="ob-qty-under">{data.UnderBuyQty ?? '-'}</span>
        <span className="ob-label-under">UNDER</span>
      </div>

      <div className="ob-spread">
        スプレッド: {data.AskPrice && data.BidPrice ? fmtPrice(data.AskPrice - data.BidPrice) : '-'}
      </div>
    </div>
  );
}
