import { useState, useEffect } from 'react';
import { fmtPrice, sideLabel } from '../utils/format';

const DEFAULT_FORM = {
  side: '2',            // 2=買い, 1=売り
  orderType: '20',      // 先物 FrontOrderType: 20=指値, 120=成行, 30=逆指値, 18=引成, 28=引指
  tradeType: '1',       // 先物: 1=新規, 2=返済
  timeInForce: '1',     // 1=当日中(FAS), 2=週内(GTC), 4=即時(FAK)
  orderExchange: '2',   // sendorder/future用取引所: 2=日通し, 23=日中, 24=夜間
  price: '',
  qty: '1',
  accountType: '2',     // 2=一般口座（先物は一般口座のみ）
  securityType: '103',  // 101=大型先物, 103=mini先物
  // 逆指値専用フィールド
  triggerPrice: '',     // トリガー価格
  underOver: '2',       // 2=以上（上抜け）, 1=以下（下抜け）
  afterHitType: '1',    // 1=成行, 2=指値
  afterHitPrice: '',    // ヒット後指値価格
};

export default function OrderForm({ onSubmit, currentPrice, symbol, exchange, closePosition, onClearClose }) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // 決済モード: closePosition が変わったらフォームを自動セット
  useEffect(() => {
    if (!closePosition) return;
    setForm((f) => ({
      ...f,
      tradeType: '2',
      side: closePosition.Side === '2' ? '1' : '2',
      qty: String(closePosition.LeavesQty ?? closePosition.Qty ?? '1'),
      price: '',
    }));
    setError(null);
  }, [closePosition]);

  const isMarket = form.orderType === '120';
  const isStop   = form.orderType === '30';

  // 逆指値の執行条件自動修正:
  //   成行ヒット後: 日通し不可→日中(23), TimeInForce:1→GTC(2)
  //   指値ヒット後: 日通し(2)+GTC(2)は不可→当日中(1)に修正
  useEffect(() => {
    if (form.orderType !== '30') return;
    setForm(f => {
      const updates = {};
      if (f.afterHitType === '1') {
        // 成行ヒット後: 日通し不可 → 日中へ
        if (f.orderExchange === '2') updates.orderExchange = '23';
        // 日中/夜間で成行ヒット後: GTC必要
        if (f.timeInForce === '1') updates.timeInForce = '2';
      } else {
        // 指値ヒット後 + 日通し: GTCは不可 → 当日中へ
        if (f.orderExchange === '2' && f.timeInForce === '2') {
          updates.timeInForce = '1';
        }
      }
      return Object.keys(updates).length ? { ...f, ...updates } : f;
    });
  }, [form.orderType, form.afterHitType, form.orderExchange]);
  // 逆指値・成行はメイン価格入力不要
  const needsPrice = !isMarket && !isStop;

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const qty = parseInt(form.qty, 10);
    if (!qty || qty <= 0) return setError('数量を入力してください');

    // 逆指値バリデーション
    if (isStop) {
      const tp = parseFloat(form.triggerPrice);
      if (!form.triggerPrice || isNaN(tp) || tp <= 0) return setError('トリガー価格を入力してください');
      if (form.afterHitType === '2') {
        const ap = parseFloat(form.afterHitPrice);
        if (!form.afterHitPrice || isNaN(ap) || ap <= 0) return setError('ヒット後指値価格を入力してください');
      }
    }

    // 通常価格バリデーション
    const price = parseFloat(needsPrice ? form.price : '0');
    if (needsPrice && (!form.price || isNaN(price))) return setError('価格を入力してください');

    setSubmitting(true);
    try {
      const tradeType = parseInt(form.tradeType, 10);
      const isClose = tradeType === 2;
      const orderPayload = {
        Symbol: symbol,
        Exchange: parseInt(form.orderExchange, 10),
        SecurityType: parseInt(form.securityType, 10),
        TradeType: tradeType,
        TimeInForce: parseInt(form.timeInForce, 10),
        Side: form.side,  // string "1" or "2"（APIスペック上はstring型）
        AccountType: parseInt(form.accountType, 10),
        Qty: qty,
        FrontOrderType: parseInt(form.orderType, 10),
        Price: price,
        ExpireDay: 0,
        // 逆指値条件
        ...(isStop && {
          ReverseLimitOrder: {
            TriggerPrice:      parseFloat(form.triggerPrice),
            UnderOver:         parseInt(form.underOver, 10),
            AfterHitOrderType: parseInt(form.afterHitType, 10),
            // 成行(1)はAfterHitPrice:0を必ず送る（省略すると4001005エラー）
            AfterHitPrice: form.afterHitType === '2' ? parseFloat(form.afterHitPrice) : 0,
          },
        }),
        // 返済条件
        ...(isClose && (closePosition
          ? { ClosePositions: [{ HoldID: closePosition.ExecutionID, Qty: qty }] }
          : { ClosePositionOrder: 0, ClosePositions: [] }
        )),
      };
      await onSubmit(orderPayload);
      setForm((f) => ({ ...f, price: '', triggerPrice: '', afterHitPrice: '' }));
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card order-form">
      <div className="card-title">注文</div>

      {/* 決済モードバナー */}
      {closePosition && (
        <div className="close-pos-banner">
          <span>
            決済モード｜{sideLabel(closePosition.Side)} {closePosition.LeavesQty ?? closePosition.Qty}枚
            {closePosition.Price ? `  @${fmtPrice(closePosition.Price)}` : ''}
          </span>
          <button type="button" className="clear-close-btn" onClick={onClearClose}>✕</button>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* 売買 */}
        <div className="form-group">
          <div className="side-buttons">
            <button
              type="button"
              className={`side-btn buy-btn ${form.side === '2' ? 'active' : ''}`}
              onClick={() => setForm((f) => ({ ...f, side: '2' }))}
            >
              買い
            </button>
            <button
              type="button"
              className={`side-btn sell-btn ${form.side === '1' ? 'active' : ''}`}
              onClick={() => setForm((f) => ({ ...f, side: '1' }))}
            >
              売り
            </button>
          </div>
        </div>

        {/* 新規/返済 */}
        <div className="form-group">
          <label className="form-label">取引区分</label>
          <select className="form-input" value={form.tradeType} onChange={set('tradeType')}>
            <option value="1">新規</option>
            <option value="2">返済</option>
          </select>
        </div>

        {/* 注文種別 */}
        <div className="form-group">
          <label className="form-label">注文種別</label>
          <select className="form-input" value={form.orderType} onChange={set('orderType')}>
            <option value="20">指値</option>
            <option value="120">成行</option>
            <option value="30">逆指値</option>
            <option value="18">引成</option>
            <option value="28">引指</option>
          </select>
        </div>

        {/* 有効期間 */}
        <div className="form-group">
          <label className="form-label">有効期間</label>
          <select className="form-input" value={form.timeInForce} onChange={set('timeInForce')}>
            <option value="1" disabled={isStop && form.afterHitType === '1'}>
              当日中{isStop && form.afterHitType === '1' ? ' (逆指値+成行不可)' : ''}
            </option>
            <option value="2">週内(GTC)</option>
            <option value="4">即時(FAK)</option>
          </select>
        </div>

        {/* 通常価格（指値・引指のみ） */}
        {needsPrice && (
          <div className="form-group">
            <label className="form-label">
              価格
              {currentPrice && (
                <button
                  type="button"
                  className="price-fill-btn"
                  onClick={() => setForm((f) => ({ ...f, price: String(currentPrice) }))}
                >
                  現在値 {fmtPrice(currentPrice)}
                </button>
              )}
            </label>
            <input
              className="form-input"
              type="number"
              value={form.price}
              onChange={set('price')}
              placeholder="価格"
              step="5"
              min="0"
            />
          </div>
        )}

        {/* 逆指値専用設定 */}
        {isStop && (
          <div className="stop-order-group">
            <div className="stop-order-label">逆指値条件</div>

            <div className="form-group">
              <label className="form-label">
                トリガー価格
                {currentPrice && (
                  <button
                    type="button"
                    className="price-fill-btn"
                    onClick={() => setForm((f) => ({ ...f, triggerPrice: String(currentPrice) }))}
                  >
                    現在値 {fmtPrice(currentPrice)}
                  </button>
                )}
              </label>
              <input
                className="form-input"
                type="number"
                value={form.triggerPrice}
                onChange={set('triggerPrice')}
                placeholder="トリガー価格"
                step="5"
                min="0"
              />
            </div>

            <div className="form-group">
              <label className="form-label">発動条件</label>
              <select className="form-input" value={form.underOver} onChange={set('underOver')}>
                <option value="2">以上（上抜け）</option>
                <option value="1">以下（下抜け）</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">ヒット後注文</label>
              <select className="form-input" value={form.afterHitType} onChange={set('afterHitType')}>
                <option value="1">成行（日中・夜間のみ）</option>
                <option value="2">指値</option>
              </select>
              {form.afterHitType === '1' && (
                <div style={{ fontSize: '11px', color: '#f0a500', marginTop: '2px' }}>
                  ※日通しは自動で日中に切替
                </div>
              )}
            </div>

            {form.afterHitType === '2' && (
              <div className="form-group">
                <label className="form-label">ヒット後指値価格</label>
                <input
                  className="form-input"
                  type="number"
                  value={form.afterHitPrice}
                  onChange={set('afterHitPrice')}
                  placeholder="指値価格"
                  step="5"
                  min="0"
                />
              </div>
            )}
          </div>
        )}

        {/* 数量 */}
        <div className="form-group">
          <label className="form-label">数量（枚）</label>
          <input
            className="form-input"
            type="number"
            value={form.qty}
            onChange={set('qty')}
            min="1"
            step="1"
          />
        </div>

        {/* 取引所（注文用） */}
        <div className="form-group">
          <label className="form-label">取引所</label>
          <select className="form-input" value={form.orderExchange} onChange={set('orderExchange')}>
            <option value="2" disabled={isStop && form.afterHitType === '1'}>
              日通し (2){isStop && form.afterHitType === '1' ? ' ※成行ヒット後不可' : ''}
            </option>
            <option value="23">日中 (23)</option>
            <option value="24">夜間 (24)</option>
          </select>
        </div>

        {/* 口座種別 */}
        <div className="form-group">
          <label className="form-label">口座</label>
          <select className="form-input" value={form.accountType} onChange={set('accountType')}>
            <option value="2">一般口座</option>
          </select>
        </div>

        {/* 銘柄種別 */}
        <div className="form-group">
          <label className="form-label">銘柄種別</label>
          <select className="form-input" value={form.securityType} onChange={set('securityType')}>
            <option value="103">mini先物 (103)</option>
            <option value="104">マイクロ先物 (104)</option>
            <option value="101">大型先物 (101)</option>
          </select>
        </div>

        {error && <div className="form-error">{error}</div>}

        <button
          type="submit"
          disabled={submitting}
          className={`submit-btn ${form.side === '2' ? 'submit-buy' : 'submit-sell'}`}
        >
          {submitting ? '送信中...' : form.side === '2' ? '買い注文' : '売り注文'}
        </button>
      </form>
    </div>
  );
}
