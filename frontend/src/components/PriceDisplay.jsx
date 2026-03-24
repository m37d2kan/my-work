import { fmtPrice, fmtChange, fmtTime, fmtVol } from '../utils/format';

export default function PriceDisplay({ data }) {
  if (!data) {
    return (
      <div className="card price-display">
        <div className="loading">データ取得中...</div>
      </div>
    );
  }

  const change = data.ChangePreviousClose;
  const changePct = data.ChangePreviousClosePercentage;
  const isUp = change >= 0;

  return (
    <div className="card price-display">
      <div className="symbol-name">{data.SymbolName ?? data.Symbol}</div>

      <div className={`current-price ${isUp ? 'up' : 'down'}`}>
        {fmtPrice(data.CurrentPrice)}
      </div>

      <div className={`price-change ${isUp ? 'up' : 'down'}`}>
        {fmtChange(change, changePct)}
      </div>

      <div className="price-time">{fmtTime(data.CurrentPriceTime)}</div>

      <div className="price-stats">
        <div className="stat">
          <span className="stat-label">始値</span>
          <span className="stat-value">{fmtPrice(data.OpeningPrice)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">高値</span>
          <span className="stat-value up">{fmtPrice(data.HighPrice)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">安値</span>
          <span className="stat-value down">{fmtPrice(data.LowPrice)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">前日終値</span>
          <span className="stat-value">{fmtPrice(data.PreviousClose)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">出来高</span>
          <span className="stat-value">{fmtVol(data.TradingVolume)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">VWAP</span>
          <span className="stat-value">{fmtPrice(data.VWAP)}</span>
        </div>
      </div>
    </div>
  );
}
