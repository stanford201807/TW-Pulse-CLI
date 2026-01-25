"""回測報告生成模組。"""

import os
from dataclasses import dataclass
from datetime import datetime
from pulse.utils.logger import get_logger

log = get_logger(__name__)

import pandas as pd


@dataclass
class BacktestReport:
    """回測報告。

    Attributes:
        ticker: 股票代碼
        strategy_name: 策略名稱
        start_date: 開始日期
        end_date: 結束日期
        initial_capital: 初始資金
        final_capital: 最終資金
        total_return: 總報酬率（%）
        annual_return: 年化報酬率（%）
        max_drawdown: 最大回撤（%）
        sharpe_ratio: 夏普比率
        win_rate: 勝率（%）
        total_trades: 總交易次數
        winning_trades: 獲利交易次數
        losing_trades: 虧損交易次數
        trades: 交易明細
        equity_curve: 權益曲線
    """

    ticker: str
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    trades: list[dict]
    equity_curve: list[dict]
    capital_state: any = None  # 動態資金狀態（可選）

    def format(self, show_trades: int = 0) -> str:
        """格式化回測報告。

        Args:
            show_trades: 顯示前 N 筆交易（0 = 全部，預設顯示全部）

        Returns:
            格式化的報告字串
        """
        days = (self.end_date - self.start_date).days
        years = days / 365.25

        # 格式化報告（明確使用 \n 確保每個項目分行）
        report = (
            f"\n[bold cyan]=== 回測報告：{self.strategy_name} - {self.ticker} ===[/bold cyan]\n"
            f"\n【回測參數】\n"
            f"期間：{self.start_date.strftime('%Y-%m-%d')} 至 {self.end_date.strftime('%Y-%m-%d')} ({days} 天 / {years:.1f} 年)\n"
            f"初始資金：NT$ {self.initial_capital:,.0f}\n"
            f"\n【績效指標】\n"
            f"總報酬率：{self.total_return:+.2f}%\n"
            f"年化報酬率：{self.annual_return:+.2f}%\n"
            f"最大回撤：{self.max_drawdown:.2f}%\n"
            f"夏普比率：{self.sharpe_ratio:.2f}\n"
            f"勝率：{self.win_rate:.1f}%\n"
            f"總交易次數：{self.total_trades} 次\n"
            f"獲利交易：{self.winning_trades} 次\n"
            f"虧損交易：{self.losing_trades} 次\n"
            f"\n【最終資產】\n"
            f"最終資金：NT$ {self.final_capital:,.0f}\n"
            f"總損益：NT$ {self.final_capital - self.initial_capital:+,.0f}\n"
        )

        if self.trades:
            report += f"\n【交易明細】（共 {len(self.trades)} 筆）\n"
            
            # 決定要顯示的交易筆數
            if show_trades > 0 and len(self.trades) > show_trades:
                trades_to_show = self.trades[:show_trades]
            else:
                trades_to_show = self.trades

            # 建立表格（每筆交易使用雙換行分隔，更易閱讀）
            for trade in trades_to_show:
                report += f"\n\n{trade['日期']} | {trade['動作']} {trade['份數']}份 @ {trade['價格']} | {trade['原因']}"

        return report

    def save_to_markdown(self, directory: str = "report", position_manager=None) -> str:
        """將回測報告保存為 Markdown 檔案。

        Args:
            directory: 保存目錄（預設 "report"）
            position_manager: 持倉管理器（用於生成詳細報表）

        Returns:
            保存的文件路徑
        """
        try:
            log.info(f"Preparing to save report to {directory}...")
            if not os.path.exists(directory):
                log.info(f"Directory {directory} does not exist. Creating it.")
                os.makedirs(directory)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{directory}/backtest_{self.ticker}_{timestamp}.md"
            abs_path = os.path.abspath(filename)
            log.info(f"Target file path: {abs_path}")

            # 建立 Markdown 報表內容
            md_report = f"""# 回測報告：{self.strategy_name} - {self.ticker}

**生成時間**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📊 回測參數

| 項目 | 數值 |
|------|------|
| 期間 | {self.start_date.strftime('%Y-%m-%d')} 至 {self.end_date.strftime('%Y-%m-%d')} |
| 初始資金 | NT$ {self.initial_capital:,.0f} |
| 回測天數 | {(self.end_date - self.start_date).days} 天 |

---

## 📈 績效指標

| 指標 | 數值 |
|------|------|
| 總報酬率 | {self.total_return:+.2f}% |
| 年化報酬率 | {self.annual_return:+.2f}% |
| 最大回撤 | {self.max_drawdown:.2f}% |
| 夏普比率 | {self.sharpe_ratio:.2f} |
| 勝率 | {self.win_rate:.1f}% |
| 總交易次數 | {self.total_trades} 次 |
| 獲利交易 | {self.winning_trades} 次 |
| 虧損交易 | {self.losing_trades} 次 |

---

## 💰 最終資產

| 項目 | 數值 |
|------|------|
| 最終資金 | NT$ {self.final_capital:,.0f} |
| 總損益 | NT$ {self.final_capital - self.initial_capital:+,.0f} |

---

## 📋 交易明細

共 {len(self.trades)} 筆交易

"""
            # 判斷是否使用動態資金詳細表格
            if self.capital_state and position_manager:
                log.info("使用動態資金詳細表格")
                # 使用 TradeReportGenerator 生成詳細表格
                from pulse.reports import TradeReportGenerator
                report_gen = TradeReportGenerator(position_manager, self.capital_state)
                
                # 只生成表格部分（不包含標題和生成時間）
                detailed_lines = report_gen.generate_detailed_report().split('\n')
                # 找到表格開始的位置（包含表頭的行）
                table_start = 0
                for i, line in enumerate(detailed_lines):
                    if '| 日期 |' in line:
                        table_start = i
                        break
                
                # 取得表格內容（從表頭到最後）
                table_content = '\n'.join(detailed_lines[table_start:])
                # 移除最後的分隔線和生成訊息
                table_content = table_content.replace('\n---\n', '').replace('*此報表由 TW-Pulse-CLI 動態資金管理模組自動生成*', '').strip()
                
                md_report += table_content + "\n"
            else:
                # 使用簡化表格（原有格式）
                log.info("使用標準交易表格")
                md_report += """| 日期 | 動作 | 份數 | 價格 | 原因 |
|------|------|------|------|------|
"""
                # 加入交易明細
                for trade in self.trades:
                    md_report += f"| {trade['日期']} | {trade['動作']} | {trade['份數']}份 | {trade['價格']} | {trade['原因']} |\n"

            md_report += """
---

*此報表由 TW-Pulse-CLI 自動生成*
"""

            # 寫入檔案
            log.info("Opening file for writing...")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(md_report)
            
            log.info(f"Successfully wrote report to {filename}")
            return filename

        except Exception as e:
            log.error(f"Failed to save report to markdown: {e}", exc_info=True)
            # 重新抛出異常以便 CLI 也能捕捉到
            raise


def calculate_metrics(
    ticker: str,
    strategy_name: str,
    position_manager,
    start_date: datetime,
    end_date: datetime,
    capital_state=None,
) -> BacktestReport:
    """計算回測績效指標。

    Args:
        ticker: 股票代碼
        strategy_name: 策略名稱
        position_manager: 持倉管理器
        start_date: 開始日期
        end_date: 結束日期
        capital_state: 動態資金狀態（可選）

    Returns:
        回測報告
    """
    initial_capital = position_manager.initial_cash
    final_capital = position_manager.equity_curve[-1]["total_equity"] if position_manager.equity_curve else initial_capital

    # 總報酬率
    total_return = ((final_capital - initial_capital) / initial_capital) * 100

    # 年化報酬率
    days = (end_date - start_date).days
    years = days / 365.25
    annual_return = ((final_capital / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0

    # 最大回撤
    max_drawdown = calculate_max_drawdown(position_manager.equity_curve)

    # 夏普比率
    sharpe_ratio = calculate_sharpe_ratio(position_manager.equity_curve)

    # 交易統計
    trades = position_manager.trades
    total_trades = len(trades)

    # 計算勝率（需要配對買賣）
    winning_trades, losing_trades, win_rate = calculate_win_rate(trades, position_manager.avg_cost)

    return BacktestReport(
        ticker=ticker,
        strategy_name=strategy_name,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        final_capital=final_capital,
        total_return=total_return,
        annual_return=annual_return,
        max_drawdown=max_drawdown,
        sharpe_ratio=sharpe_ratio,
        win_rate=win_rate,
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        trades=[t.to_dict() for t in trades],
        equity_curve=position_manager.equity_curve,
        capital_state=capital_state,  # 傳遞動態資金狀態
    )


def calculate_max_drawdown(equity_curve: list[dict]) -> float:
    """計算最大回撤。

    Args:
        equity_curve: 權益曲線

    Returns:
        最大回撤（百分比）
    """
    if not equity_curve:
        return 0.0

    peak = equity_curve[0]["total_equity"]
    max_dd = 0.0

    for point in equity_curve:
        equity = point["total_equity"]
        if equity > peak:
            peak = equity
        dd = ((peak - equity) / peak) * 100
        if dd > max_dd:
            max_dd = dd

    return max_dd


def calculate_sharpe_ratio(equity_curve: list[dict], risk_free_rate: float = 0.02) -> float:
    """計算夏普比率。

    Args:
        equity_curve: 權益曲線
        risk_free_rate: 無風險利率（年化）

    Returns:
        夏普比率
    """
    if len(equity_curve) < 2:
        return 0.0

    # 計算每日報酬率
    returns = []
    for i in range(1, len(equity_curve)):
        prev_equity = equity_curve[i - 1]["total_equity"]
        curr_equity = equity_curve[i]["total_equity"]
        daily_return = (curr_equity - prev_equity) / prev_equity
        returns.append(daily_return)

    if not returns:
        return 0.0

    # 使用 pandas 計算
    returns_series = pd.Series(returns)
    mean_return = returns_series.mean() * 252  # 年化
    std_return = returns_series.std() * (252**0.5)  # 年化

    if std_return == 0:
        return 0.0

    sharpe = (mean_return - risk_free_rate) / std_return
    return sharpe


def calculate_win_rate(trades: list, avg_cost: float) -> tuple[int, int, float]:
    """計算勝率。

    Args:
        trades: 交易記錄
        avg_cost: 平均成本

    Returns:
        (獲利次數, 虧損次數, 勝率)
    """
    if not trades:
        return 0, 0, 0.0

    winning = 0
    losing = 0

    # 簡化版：根據賣出價格與平均成本比較
    for trade in trades:
        if trade.action == "賣出":
            if trade.price > avg_cost:
                winning += 1
            else:
                losing += 1

    total = winning + losing
    win_rate = (winning / total * 100) if total > 0 else 0.0

    return winning, losing, win_rate
