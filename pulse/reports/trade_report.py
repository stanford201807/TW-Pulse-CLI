"""動態資金交易報表生成模組。"""

from datetime import datetime
from typing import Any

from pulse.core.backtest.position import PositionManager, Trade
from pulse.core.capital import CapitalState
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class TradeReportGenerator:
    """動態資金交易報表生成器。

    生成包含動態資金變化的詳細交易報表。
    """

    def __init__(self, position_manager: PositionManager, capital_state: CapitalState | None = None):
        """初始化報表生成器。

        Args:
            position_manager: 持倉管理器
            capital_state: 資金狀態（可選）
        """
        self.position_manager = position_manager
        self.capital_state = capital_state

    def generate_detailed_report(self) -> str:
        """生成詳細交易報表（Markdown 格式）。

        Returns:
            Markdown 格式的詳細報表
        """
        if not self.position_manager.trades:
            return "# 交易報表\n\n無交易記錄。"

        report_lines = []
        report_lines.append("# 動態資金交易報表\n")
        report_lines.append(f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_lines.append("---\n")

        # 欄位寬度定義（緊湊型）
        W_DATE = 10
        W_ACTION = 4
        W_PRICE = 9
        W_PEAK = 9
        W_CHANGE = 7
        W_POS = 8
        W_AMOUNT = 10
        W_SHARES = 6
        W_CAPITAL = 11
        W_NOTE = 12

        # 動態生成表頭（確保對齊）
        h_date = self._pad_visual("日期", W_DATE, '<')
        h_action = self._pad_visual("動作", W_ACTION, '<')
        h_price = self._pad_visual("成交價", W_PRICE, '>')
        h_peak = self._pad_visual("持倉最高", W_PEAK, '>')
        h_change = self._pad_visual("漲跌%", W_CHANGE, '>')
        h_pos = self._pad_visual("資金份數", W_POS, '>')
        h_amount = self._pad_visual("收付金額", W_AMOUNT, '>')
        h_shares = self._pad_visual("庫存", W_SHARES, '>')
        h_capital = self._pad_visual("當前總資金", W_CAPITAL, '>')
        h_note = self._pad_visual("備註", W_NOTE, '<')

        header = (
            f"| {h_date} | {h_action} | {h_price} | {h_peak} | {h_change} | "
            f"{h_pos} | {h_amount} | {h_shares} | {h_capital} | {h_note} |"
        )
        
        # 動態生成分隔線
        separator = (
            f"| {'-' * W_DATE} | {'-' * W_ACTION} | {'-' * W_PRICE} | {'-' * W_PEAK} | {'-' * W_CHANGE} | "
            f"{'-' * W_POS} | {'-' * W_AMOUNT} | {'-' * W_SHARES} | {'-' * W_CAPITAL} | {'-' * W_NOTE} |"
        )

        report_lines.append(header)
        report_lines.append(separator)

        # 初始化追蹤變數
        initial_capital = self.capital_state.initial_capital if self.capital_state else self.position_manager.initial_cash
        num_positions = self.capital_state.num_positions if self.capital_state else 10
        
        current_shares = 0  # 當前庫存股數
        peak_price = 0.0    # 波段最高價
        total_capital = initial_capital  # 當前總資金（動態更新）
        realized_pnl = 0.0  # 已實現損益
        last_trade_price = 0.0  # 上次交易價格（用於計算漲跌%）
        position_count = 0.0  # 當前持倉份數（實際買賣次數）
        
        # 追蹤買進成本（用於計算賣出損益）
        buy_cost_queue = []  # [(shares, price), ...]
        total_buy_cost = 0.0  # 當前持倉的總成本
        
        cumulative_invested = 0.0  # 累積投入金額（用於計算份數）
        cumulative_withdrawn = 0.0  # 累積提取金額

        # 生成每筆交易記錄
        for trade in self.position_manager.trades:
            # 處理買進
            if trade.action == "買進":
                current_shares += trade.shares
                cumulative_invested += trade.amount
                position_count += 1.0  # 買進增加 1 份
                
                # 記錄買進成本
                buy_cost_queue.append((trade.shares, trade.price))
                total_buy_cost += trade.amount
                
            # 處理賣出
            else:  # 賣出
                sell_shares = trade.shares
                sell_amount = trade.amount
                cumulative_withdrawn += sell_amount
                
                # 計算此次賣出的成本（FIFO）
                sell_cost = 0.0
                remaining_sell = sell_shares
                
                while remaining_sell > 0 and buy_cost_queue:
                    buy_shares, buy_price = buy_cost_queue[0]
                    
                    if buy_shares <= remaining_sell:
                        # 全部賣出這批
                        sell_cost += buy_shares * buy_price
                        remaining_sell -= buy_shares
                        buy_cost_queue.pop(0)
                    else:
                        # 部分賣出這批
                        sell_cost += remaining_sell * buy_price
                        buy_cost_queue[0] = (buy_shares - remaining_sell, buy_price)
                        remaining_sell = 0
                
                # 計算已實現損益
                trade_pnl = sell_amount - sell_cost
                realized_pnl += trade_pnl
                
                # 更新總資金
                total_capital = initial_capital + realized_pnl
                
                # 更新持倉總成本
                total_buy_cost -= sell_cost
                current_shares -= sell_shares
                
                # 更新份數：全數清倉 or 減碼 1 份
                if current_shares == 0:
                    position_count = 0.0  # 全數清倉
                else:
                    position_count -= 1.0  # 減碼 1 份

            # 更新波段最高價（僅在持倉期間追蹤）
            if current_shares > 0:
                if trade.price > peak_price:
                    peak_price = trade.price
            else:
                # 清倉後重置波段最高價
                peak_price = 0.0

            # 計算漲跌百分比（相對於上次交易價格）
            if last_trade_price > 0:
                price_change_pct = ((trade.price - last_trade_price) / last_trade_price) * 100
                change_str = f"{price_change_pct:+.1f}%"  # 使用 + 號顯示正數
            else:
                change_str = "-"
            
            # 更新上次交易價格
            last_trade_price = trade.price

            # 收付金額
            amount_str = f"-{trade.amount:,.0f}" if trade.action == "買進" else f"+{trade.amount:,.0f}"

            # 資金份數
            position_str = f"{position_count:.1f}/{num_positions}"

            # 持倉最高價
            peak_str = f"{peak_price:,.2f}" if peak_price > 0 else "-"

            # 備註（從 reason 提取）
            note = self._extract_note_from_reason(trade.reason)

            # 生成行（使用視覺寬度對齊）
            date_col = self._pad_visual(trade.date.strftime('%Y-%m-%d'), W_DATE, '<')
            action_col = self._pad_visual(trade.action, W_ACTION, '<')
            price_col = self._pad_visual(f"{trade.price:,.2f}", W_PRICE, '>')
            peak_col = self._pad_visual(peak_str, W_PEAK, '>')
            change_col = self._pad_visual(change_str, W_CHANGE, '>')
            position_col = self._pad_visual(position_str, W_POS, '>')
            amount_col = self._pad_visual(amount_str, W_AMOUNT, '>')
            shares_col = self._pad_visual(str(current_shares), W_SHARES, '>')
            total_cap_col = self._pad_visual(f"{total_capital:,.0f}", W_CAPITAL, '>')
            note_col = self._pad_visual(note, W_NOTE, '<')
            
            row = (
                f"| {date_col} "
                f"| {action_col} "
                f"| {price_col} "
                f"| {peak_col} "
                f"| {change_col} "
                f"| {position_col} "
                f"| {amount_col} "
                f"| {shares_col} "
                f"| {total_cap_col} "
                f"| {note_col} |"
            )
            report_lines.append(row)

        # 添加當前持倉狀態（回測結束日）
        if self.position_manager.equity_curve and current_shares > 0:
            last_equity = self.position_manager.equity_curve[-1]
            last_date = last_equity["date"]
            last_price = last_equity["price"]
            last_total_equity = last_equity["total_equity"]
            
            # 計算漲跌（相對於上次交易價格）
            if last_trade_price > 0:
                price_change_pct = ((last_price - last_trade_price) / last_trade_price) * 100
                change_str = f"{price_change_pct:+.1f}%"
            else:
                change_str = "-"
            
            # 生成當前狀態行（使用實際追蹤的 position_count）
            date_col = self._pad_visual(last_date.strftime('%Y-%m-%d'), W_DATE, '<')
            action_col = self._pad_visual("持有", W_ACTION, '<')
            price_col = self._pad_visual(f"{last_price:,.2f}", W_PRICE, '>')
            peak_col = self._pad_visual(f"{peak_price:,.2f}" if peak_price > 0 else "-", W_PEAK, '>')
            change_col = self._pad_visual(change_str, W_CHANGE, '>')
            position_col = self._pad_visual(f"{position_count:.1f}/{num_positions}", W_POS, '>')  # 使用實際份數
            amount_col = self._pad_visual("-", W_AMOUNT, '>')
            shares_col = self._pad_visual(str(current_shares), W_SHARES, '>')
            total_cap_col = self._pad_visual(f"{last_total_equity:,.0f}", W_CAPITAL, '>')
            note_col = self._pad_visual("當前狀態", W_NOTE, '<')
            
            current_row = (
                f"| {date_col} "
                f"| {action_col} "
                f"| {price_col} "
                f"| {peak_col} "
                f"| {change_col} "
                f"| {position_col} "
                f"| {amount_col} "
                f"| {shares_col} "
                f"| {total_cap_col} "
                f"| {note_col} |"
            )
            report_lines.append(current_row)

        report_lines.append(separator)
        report_lines.append("\n*此報表由 TW-Pulse-CLI 動態資金管理模組自動生成*\n")


        return "\n".join(report_lines)

    def _get_visual_width(self, text: str) -> int:
        """計算字串的視覺寬度（中文字算2格，英數算1格）。"""
        width = 0
        for char in text:
            # 判斷是否為寬字符 (簡單判斷：ASCII 以外視為寬字)
            if ord(char) > 127:
                width += 2
            else:
                width += 1
        return width

    def _pad_visual(self, text: str, width: int, align: str = '<') -> str:
        """依照視覺寬度進行填充。"""
        visual_w = self._get_visual_width(text)
        padding_len = max(0, width - visual_w)
        padding = " " * padding_len
        
        if align == '<':
            return text + padding
        elif align == '>':
            return padding + text
        else:  # center
            left = padding_len // 2
            right = padding_len - left
            return (" " * left) + text + (" " * right)

    def _extract_note_from_reason(self, reason: str) -> str:
        """從交易原因提取簡短備註。

        Args:
            reason: 交易原因

        Returns:
            簡短備註
        """
        # 簡化 reason 內容
        if "站上年線" in reason:
            return "站上年線"
        elif "RSI" in reason:
            return "RSI抄底"
        elif "加碼" in reason:
            return "農夫加碼"
        elif "減碼" in reason:
            return "農夫減碼"
        elif "停利" in reason:
            return "移動停利"
        elif "防禦" in reason:
            return "防禦機制"
        else:
            # 截取前 10 個字元
            return reason[:10] + "..." if len(reason) > 10 else reason

    def generate_summary_stats(self) -> dict[str, Any]:
        """生成統計摘要。

        Returns:
            統計數據字典
        """
        trades = self.position_manager.trades
        if not trades:
            return {}

        buy_trades = [t for t in trades if t.action == "買進"]
        sell_trades = [t for t in trades if t.action == "賣出"]

        total_buy_amount = sum(t.amount for t in buy_trades)
        total_sell_amount = sum(t.amount for t in sell_trades)

        return {
            "total_trades": len(trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "total_buy_amount": total_buy_amount,
            "total_sell_amount": total_sell_amount,
            "net_cash_flow": total_sell_amount - total_buy_amount,
        }
