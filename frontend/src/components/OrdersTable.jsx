import { fmtPrice, sideLabel, orderTypeLabel, orderStatusLabel } from '../utils/format';

const CANCELLABLE_STATUSES = [5, 6, 7]; // 仮受付, 受付, 順番待ち

export default function OrdersTable({ orders, onCancel, onRefresh }) {
  return (
    <div className="data-table-wrap">
      <div className="table-header">
        <button className="refresh-btn" onClick={onRefresh}>更新</button>
      </div>
      {orders.length === 0 ? (
        <div className="empty">注文なし</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>注文ID</th>
              <th>シンボル</th>
              <th>売買</th>
              <th>種別</th>
              <th>価格</th>
              <th>数量</th>
              <th>残数量</th>
              <th>状態</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.ID}>
                <td className="order-id">{o.ID}</td>
                <td>{o.Symbol}</td>
                <td className={o.Side === '2' ? 'up' : 'down'}>{sideLabel(o.Side)}</td>
                <td>{orderTypeLabel(o.FrontOrderType)}</td>
                <td>{o.Price ? fmtPrice(o.Price) : '成行'}</td>
                <td>{o.OrderQty}</td>
                <td>{o.CumQty != null ? o.OrderQty - o.CumQty : '-'}</td>
                <td>{orderStatusLabel(o.State)}</td>
                <td>
                  {CANCELLABLE_STATUSES.includes(o.State) && (
                    <button
                      className="cancel-btn"
                      onClick={() => onCancel(o.ID)}
                    >
                      取消
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
