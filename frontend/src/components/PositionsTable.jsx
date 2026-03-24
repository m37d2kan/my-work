import { fmtPrice, sideLabel } from '../utils/format';

export default function PositionsTable({ positions, onRefresh, onClose }) {
  return (
    <div className="data-table-wrap">
      <div className="table-header">
        <button className="refresh-btn" onClick={onRefresh}>更新</button>
      </div>
      {positions.length === 0 ? (
        <div className="empty">ポジションなし</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>シンボル</th>
              <th>売買</th>
              <th>数量</th>
              <th>平均取得価格</th>
              <th>評価損益</th>
              <th>期限日</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p, i) => (
              <tr key={p.ExecutionID ?? i}>
                <td>{p.Symbol}</td>
                <td className={p.Side === '2' ? 'up' : 'down'}>{sideLabel(p.Side)}</td>
                <td>{p.LeavesQty ?? p.Qty}</td>
                <td>{fmtPrice(p.Price)}</td>
                <td className={
                  p.ProfitLoss > 0 ? 'up' : p.ProfitLoss < 0 ? 'down' : ''
                }>
                  {p.ProfitLoss != null ? `${p.ProfitLoss > 0 ? '+' : ''}${fmtPrice(p.ProfitLoss)}` : '-'}
                </td>
                <td>{p.ExpireDay ?? '-'}</td>
                <td>
                  <button className="close-pos-btn" onClick={() => onClose(p)}>
                    決済
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
