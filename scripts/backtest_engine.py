"""NDI Backtesting Engine - Local Version"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class NDI_Backtest:
    """Motor de backtesting para señales NDI"""
    
    def __init__(self, 
                 initial_capital: float = 100_000,
                 threshold: float = 1.5,
                 hold_days: int = 5,
                 transaction_cost: float = 0.001,
                 allow_shorts: bool = True,
                 use_confidence_filter: bool = True,
                 min_confidence: str = 'Medium'):
        
        self.initial_capital = initial_capital
        self.threshold = threshold
        self.hold_days = hold_days
        self.transaction_cost = transaction_cost
        self.allow_shorts = allow_shorts
        self.use_confidence_filter = use_confidence_filter
        self.min_confidence = min_confidence
        self.results = {}
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Genera señales basadas en NDI"""
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        signals['entry_price'] = np.nan
        signals['exit_price'] = np.nan
        signals['return'] = 0.0
        signals['position_days'] = 0
        
        position = 0
        entry_day = 0
        entry_price = 0
        
        for i, (idx, row) in enumerate(df.iterrows()):
            ndi = row['ndi']
            confidence = row.get('confidence', 'Low')
            price = row['close']
            
            if self.use_confidence_filter:
                conf_ok = confidence in ['High', 'Medium'] if self.min_confidence == 'Medium' else confidence == 'High'
            else:
                conf_ok = True
            
            if position == 0:
                if conf_ok and ndi < -self.threshold:
                    position = 1
                    entry_day = i
                    entry_price = price
                    signals.loc[idx, 'signal'] = 1
                    signals.loc[idx, 'entry_price'] = price
                elif self.allow_shorts and conf_ok and ndi > self.threshold:
                    position = -1
                    entry_day = i
                    entry_price = price
                    signals.loc[idx, 'signal'] = -1
                    signals.loc[idx, 'entry_price'] = price
            
            elif position != 0:
                days_held = i - entry_day
                if days_held >= self.hold_days:
                    exit_price = price
                    if position == 1:
                        ret = (exit_price - entry_price) / entry_price
                    else:
                        ret = (entry_price - exit_price) / entry_price
                    
                    ret -= self.transaction_cost * 2
                    
                    signals.loc[idx, 'exit_price'] = exit_price
                    signals.loc[idx, 'return'] = ret
                    signals.loc[idx, 'position_days'] = days_held
                    
                    position = 0
                    entry_day = 0
                    entry_price = 0
        
        if position != 0:
            exit_price = df.iloc[-1]['close']
            days_held = len(df) - entry_day - 1
            if position == 1:
                ret = (exit_price - entry_price) / entry_price
            else:
                ret = (entry_price - exit_price) / entry_price
            ret -= self.transaction_cost * 2
            signals.iloc[-1, signals.columns.get_loc('exit_price')] = exit_price
            signals.iloc[-1, signals.columns.get_loc('return')] = ret
            signals.iloc[-1, signals.columns.get_loc('position_days')] = days_held
        
        return signals
    
    def run_backtest(self, df: pd.DataFrame) -> Dict:
        """Ejecuta backtest completo"""
        tickers = df['ticker'].unique()
        all_trades = []
        equity_curves = []
        
        for ticker in tickers:
            ticker_df = df[df['ticker'] == ticker].copy().sort_values('date')
            if len(ticker_df) < self.hold_days + 10:
                continue
            
            signals = self.generate_signals(ticker_df)
            
            equity = self.initial_capital
            equity_curve = [equity]
            dates = ticker_df['date'].values
            
            for ret in signals['return'].values:
                if ret != 0:
                    equity = equity * (1 + ret)
                equity_curve.append(equity)
            
            trades = signals[signals['return'] != 0].copy()
            trades['ticker'] = ticker
            trades['cumulative_return'] = (1 + trades['return']).cumprod() - 1
            all_trades.append(trades)
            
            equity_curves.append(pd.DataFrame({
                'date': list(dates) + [dates[-1]],
                'equity': equity_curve,
                'ticker': ticker
            }))
        
        if not all_trades:
            return {'error': 'No trades generated'}
        
        all_trades_df = pd.concat(all_trades, ignore_index=True)
        equity_df = pd.concat(equity_curves, ignore_index=True)
        
        total_return = (equity_df.groupby('ticker')['equity'].last() / self.initial_capital - 1).mean()
        returns_series = all_trades_df['return'].values
        winning_trades = returns_series[returns_series > 0]
        losing_trades = returns_series[returns_series <= 0]
        
        hit_rate = len(winning_trades) / len(returns_series) if len(returns_series) > 0 else 0
        profit_factor = abs(winning_trades.sum() / losing_trades.sum()) if len(losing_trades) > 0 and losing_trades.sum() != 0 else np.inf
        
        daily_returns = equity_df.groupby('date')['equity'].pct_change().fillna(0).values
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0
        
        cumulative = equity_df.groupby('date')['equity'].last().values
        peak = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min()
        calmar = (total_return / abs(max_drawdown)) if max_drawdown != 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': (1 + total_return) ** (252 / len(equity_df['date'].unique())) - 1,
            'sharpe_ratio': sharpe,
            'calmar_ratio': calmar,
            'max_drawdown': max_drawdown,
            'hit_rate': hit_rate,
            'profit_factor': profit_factor,
            'num_trades': len(returns_series),
            'num_winning_trades': len(winning_trades),
            'num_losing_trades': len(losing_trades),
            'trades': all_trades_df,
            'equity_curve': equity_df
        }


def generate_synthetic_data(days: int = 500, tickers: List[str] = None):
    """Genera datos sintéticos realistas"""
    if tickers is None:
        tickers = ['NVDA', 'AAPL', 'MSFT']
    
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    data = []
    for ticker in tickers:
        price = 100
        ndi_series = []
        
        for i, d in enumerate(dates):
            # Precio con tendencia
            price *= (1 + np.random.normal(0.0005, 0.02))
            
            # NDI con autocorrelación
            if i == 0:
                ndi = np.random.normal(0, 1)
            else:
                ndi = 0.92 * ndi_series[-1] + np.random.normal(0, 0.25)
            ndi = np.clip(ndi, -3, 3)
            ndi_series.append(ndi)
            
            # Confianza
            if abs(ndi) > 1.5:
                conf = 'High' if np.random.rand() > 0.3 else 'Medium'
            elif abs(ndi) > 0.5:
                conf = 'Medium'
            else:
                conf = 'Low'
            
            data.append({'date': d, 'ticker': ticker, 'close': price, 'ndi': ndi, 'confidence': conf})
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    print("=" * 70)
    print("NDI Backtesting Engine - Local Demo")
    print("=" * 70)
    
    # Generar datos
    df = generate_synthetic_data(days=500)
    print(f"\n📊 Generated {len(df)} rows for {df['ticker'].nunique()} tickers")
    
    # Probar diferentes thresholds
    print("\n📊 BACKTEST RESULTS BY THRESHOLD")
    print("=" * 70)
    
    for th in [1.0, 1.5, 2.0, 2.5]:
        bt = NDI_Backtest(threshold=th, hold_days=5, allow_shorts=True)
        results = bt.run_backtest(df)
        
        if 'error' in results:
            print(f"\nThreshold {th}: {results['error']}")
            continue
        
        print(f"\n🔹 THRESHOLD = {th}")
        print(f"   Total Return: {results['total_return']:.2%}")
        print(f"   Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"   Hit Rate: {results['hit_rate']:.2%}")
        print(f"   Profit Factor: {results['profit_factor']:.2f}")
        print(f"   Max Drawdown: {results['max_drawdown']:.2%}")
        print(f"   Trades: {results['num_trades']}")
    
    print("\n" + "=" * 70)
    print("✅ Backtest completed")
    print("=" * 70)
