"""測試動態資金管理模組。"""

import pytest

from pulse.core.capital import CapitalState, DynamicCapitalManager


class TestCapitalState:
    """測試 CapitalState 資料類別。"""

    def test_initial_state(self):
        """測試初始狀態建立。"""
        state = CapitalState(initial_capital=1_000_000, current_capital=1_000_000)
        
        assert state.initial_capital == 1_000_000
        assert state.current_capital == 1_000_000
        assert state.num_positions == 10
        assert state.realized_pnl == 0.0
        assert state.peak_price == 0.0

    def test_invalid_initial_capital(self):
        """測試無效初始資金。"""
        with pytest.raises(ValueError, match="初始資金必須大於 0"):
            CapitalState(initial_capital=0, current_capital=0)

    def test_invalid_num_positions(self):
        """測試無效份數。"""
        with pytest.raises(ValueError, match="總份數必須大於 0"):
            CapitalState(
                initial_capital=1_000_000,
                current_capital=1_000_000,
                num_positions=0
            )


class TestDynamicCapitalManager:
    """測試 DynamicCapitalManager 類別。"""

    def test_initialization(self):
        """測試初始化。"""
        manager = DynamicCapitalManager(initial_capital=1_000_000, num_positions=10)
        
        assert manager.get_current_capital() == 1_000_000
        assert manager.get_position_size() == 100_000
        assert manager.state.num_positions == 10

    def test_profit_increases_capital(self):
        """測試盈利後總資金增加。"""
        manager = DynamicCapitalManager(initial_capital=1_000_000)
        
        # 盈利 50,000
        manager.update_capital(profit_or_loss=50_000)
        
        assert manager.get_current_capital() == 1_050_000
        assert manager.state.realized_pnl == 50_000
        # 每份金額應該增加到 105,000
        assert manager.get_position_size() == 105_000

    def test_loss_decreases_capital(self):
        """測試虧損後總資金減少。"""
        manager = DynamicCapitalManager(initial_capital=1_000_000)
        
        # 虧損 30,000
        manager.update_capital(profit_or_loss=-30_000)
        
        assert manager.get_current_capital() == 970_000
        assert manager.state.realized_pnl == -30_000
        # 每份金額應該減少到 97,000
        assert manager.get_position_size() == 97_000

    def test_multiple_trades(self):
        """測試多次交易累積損益。"""
        manager = DynamicCapitalManager(initial_capital=2_000_000)
        
        # 第一次盈利 100,000
        manager.update_capital(profit_or_loss=100_000)
        assert manager.get_current_capital() == 2_100_000
        
        # 第二次虧損 50,000
        manager.update_capital(profit_or_loss=-50_000)
        assert manager.get_current_capital() == 2_050_000
        
        # 累積損益
        assert manager.state.realized_pnl == 50_000

    def test_position_size_calculation(self):
        """測試份額計算正確性。"""
        manager = DynamicCapitalManager(initial_capital=1_000_000, num_positions=10)
        assert manager.get_position_size() == 100_000
        
        # 改變資金後
        manager.update_capital(profit_or_loss=200_000)
        assert manager.get_position_size() == 120_000

    def test_calculate_shares(self):
        """測試股數計算（向下取整）。"""
        manager = DynamicCapitalManager(initial_capital=1_000_000, num_positions=10)
        
        # 每份 100,000，股價 507
        # 100,000 / 507 = 197.23... -> 197 股
        shares = manager.calculate_shares(price=507.0)
        assert shares == 197
        
        # 股價變化後
        shares = manager.calculate_shares(price=1000.0)
        assert shares == 100

    def test_calculate_shares_invalid_price(self):
        """測試無效股價。"""
        manager = DynamicCapitalManager(initial_capital=1_000_000)
        
        with pytest.raises(ValueError, match="股價必須大於 0"):
            manager.calculate_shares(price=0)
        
        with pytest.raises(ValueError, match="股價必須大於 0"):
            manager.calculate_shares(price=-100)

    def test_update_peak_price(self):
        """測試波段最高價更新。"""
        manager = DynamicCapitalManager(initial_capital=1_000_000)
        
        manager.update_peak_price(500.0)
        assert manager.state.peak_price == 500.0
        
        # 更高價格會更新
        manager.update_peak_price(600.0)
        assert manager.state.peak_price == 600.0
        
        # 較低價格不會更新
        manager.update_peak_price(550.0)
        assert manager.state.peak_price == 600.0

    def test_calculate_drawdown_percent(self):
        """測試回落百分比計算。"""
        manager = DynamicCapitalManager(initial_capital=1_000_000)
        
        # 設定最高價 1000
        manager.update_peak_price(1000.0)
        
        # 當前價 800，回落 20%
        drawdown = manager.calculate_drawdown_percent(800.0)
        assert drawdown == pytest.approx(20.0, rel=1e-5)
        
        # 當前價 900，回落 10%
        drawdown = manager.calculate_drawdown_percent(900.0)
        assert drawdown == pytest.approx(10.0, rel=1e-5)
        
        # 當前價高於最高價，回落 0%
        drawdown = manager.calculate_drawdown_percent(1100.0)
        assert drawdown == 0.0

    def test_record_trade(self):
        """測試交易記錄。"""
        manager = DynamicCapitalManager(initial_capital=1_000_000)
        
        manager.record_trade(price=500.0, is_buy=True)
        assert manager.state.last_trade_price == 500.0
        
        manager.record_trade(price=520.0, is_buy=False)
        assert manager.state.last_trade_price == 520.0

    def test_get_status_summary(self):
        """測試狀態摘要輸出。"""
        manager = DynamicCapitalManager(initial_capital=1_000_000)
        manager.update_capital(profit_or_loss=50_000)
        
        summary = manager.get_status_summary()
        
        assert "1,000,000" in summary
        assert "1,050,000" in summary
        assert "+50,000" in summary or "50,000" in summary


class TestDynamicCapitalManagerIntegration:
    """整合測試：模擬真實交易流程。"""

    def test_farmer_strategy_simulation(self):
        """模擬農夫策略交易流程。"""
        # 初始資金 2,000,000，分 10 份
        manager = DynamicCapitalManager(initial_capital=2_000_000, num_positions=10)
        
        # 交易 1: 初始買進 @ 507
        shares_1 = manager.calculate_shares(price=507.0)
        assert shares_1 == 394  # 200,000 / 507 = 394.47... -> 394
        cost_1 = shares_1 * 507.0
        manager.update_peak_price(507.0)
        manager.record_trade(price=507.0, is_buy=True)
        
        # 交易 2: 加碼買進 @ 537（假設已盈利）
        # 假設前面的持股浮盈，但未實現
        manager.update_peak_price(543.0)
        shares_2 = manager.calculate_shares(price=537.0)
        assert shares_2 == 372  # 200,000 / 537 = 372.43... -> 372
        
        # 交易 3: 減碼賣出 @ 514（實現部分盈虧）
        # 假設賣出 377 股，計算損益
        sell_shares = 377
        sell_price = 514.0
        avg_cost = (cost_1 + shares_2 * 537.0) / (shares_1 + shares_2)
        pnl = sell_shares * (sell_price - avg_cost)
        
        manager.update_capital(profit_or_loss=pnl)
        
        # 驗證總資金有變化
        assert manager.get_current_capital() != 2_000_000

    def test_dynamic_position_sizing(self):
        """測試動態份額隨盈虧變化。"""
        manager = DynamicCapitalManager(initial_capital=1_000_000, num_positions=10)
        
        # 初始每份 100,000
        initial_size = manager.get_position_size()
        assert initial_size == 100_000
        
        # 盈利 10% 後，每份變為 110,000
        manager.update_capital(profit_or_loss=100_000)
        new_size = manager.get_position_size()
        assert new_size == 110_000
        assert new_size > initial_size
        
        # 虧損 20% 後，每份變為 88,000
        manager.update_capital(profit_or_loss=-200_000)
        final_size = manager.get_position_size()
        assert final_size == 90_000  # (1,000,000 + 100,000 - 200,000) / 10
        assert final_size < initial_size
