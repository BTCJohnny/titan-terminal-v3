FULL UNIVERSE BACKTEST REPORT — with derivatives data
Generated: 20260322
============================================================

## 1. SUMMARY

  Phase 4 files found  : 66
  Symbols scanned      : 33
  Total survivors      : 330
  Walk-forward passes  : 293
  Total graduates      : 101
  Unique strategies    : 21
  Unique sym×strat     : 99

## 2. STRATEGY LEADERBOARD (by cross-symbol consistency)

  #    Strategy                                          Syms  Grads   AvgPF  Symbols
  ---  ------------------------------------------------  ----  -----  ------  ------------------------------
  1    E9: OI Surge Standalone (ETH)                       16     19    3.24  AAVE,AERO,ASTER,BNB,DOGE,ENA,ETH...
  2    E7: OI Surge + BB Squeeze (ETH)                     12     14    5.73  AERO,ENA,ETH,LINK,PENDLE,PUMP,SK...
  3    E8: OI Surge + RSI Oversold (ETH)                    8      8    7.87  0G,ASTER,FARTCOIN,HYPE,RENDER,SK...
  4    E5: Death Cross + Crowd Long                         6      7    4.20  AVAX,BNB,BTC,ENA,LINK,SUI
  5    E1: MACD Rollover + Death Cross                      6      9    2.88  AERO,APT,BTC,ENS,FLOW,JUP
  6    E10: OI Div Bullish + RSI Oversold (ETH)             5      5    7.87  FARTCOIN,FLOW,LINK,RENDER,XPL
  7    C1: OI Accumulation                                  5      5    7.68  ASTER,FARTCOIN,FLOW,LINK,XPL
  8    E11: Triple Short (MACD + Death Cross + Crowd Long)     4      4    3.79  AVAX,DOGE,ENA,XRP
  9    G12: MACD Bullish + ADX Strong (SHORT)               4      5    3.62  ETH,FLOW,PENDLE,SUI
  10   E2: MACD Rollover + Crowd Long                       4      5    3.27  ASTER,BTC,ENA,XRP
  11   C2: OI Distribution                                  4      4    2.85  AERO,ENS,PUMP,SOL
  12   G8: Triple Energy Buildup                            3      3    4.66  FARTCOIN,PUMP,SYRUP
  13   F6: Fear Oversold Bounce                             3      3    3.17  0G,SKY,ZRO
  14   A4: Fear & Greed Extreme Fear Buy                    2      2    4.42  SKYAI,ZRO
  15   D1: Volatility Squeeze Breakout                      1      1   18.67  XPL
  16   B2: OI Breakout Long                                 1      1   13.68  PUMP
  17   G7: Compressed Breakdown Bear                        1      1    3.83  AERO
  18   B3: OI Breakout Short                                1      1    3.42  LINK
  19   E3: BB Upper Touch + Death Cross                     1      1    2.99  AERO
  20   E4: BB Upper + Crowd Long                            1      2    2.59  DOGE
  21   E12: RSI OB Short + Death Cross (ETH)                1      1    1.93  ENS

## 3. PER-SYMBOL SUMMARY

  0G (1h): 1 graduate
    E8: OI Surge + RSI Oversold (ETH) [target1_atr_mult=4.5]  PF:4.33  WR:75.0%  Trades:12  DD:4.0%  AvgR:0.82
  0G (4h): 1 graduate
    F6: Fear Oversold Bounce [stop_atr_mult=1.0]  PF:2.63  WR:45.5%  Trades:11  DD:4.0%  AvgR:0.95
  AAVE (1h): 1 graduate
    E9: OI Surge Standalone (ETH) [oi_surge_pct=3.0]  PF:2.94  WR:68.8%  Trades:32  DD:7.6%  AvgR:0.65
  AERO (1h): 3 graduates
    E7: OI Surge + BB Squeeze (ETH) [bb_squeeze_pct=0.375]  PF:3.69  WR:65.4%  Trades:26  DD:4.0%  AvgR:1.09
    (SHORT) G7: Compressed Breakdown Bear [target1_atr_mult=4.5]  PF:3.83  WR:63.6%  Trades:11  DD:4.0%  AvgR:1.16
    E9: OI Surge Standalone (ETH) [stop_atr_mult=1.5]  PF:2.62  WR:54.5%  Trades:44  DD:9.6%  AvgR:0.82
  AERO (4h): 3 graduates
    (SHORT) C2: OI Distribution [target2_atr_mult=7.5]  PF:4.45  WR:72.7%  Trades:11  DD:2.0%  AvgR:0.94
    (SHORT) E3: BB Upper Touch + Death Cross [target1_atr_mult=3.75]  PF:2.99  WR:60.0%  Trades:10  DD:4.0%  AvgR:0.88
    (SHORT) E1: MACD Rollover + Death Cross [target2_atr_mult=9.0]  PF:2.97  WR:70.0%  Trades:10  DD:5.9%  AvgR:0.68
  APT (1h): 1 graduate
    (SHORT) E1: MACD Rollover + Death Cross [target2_atr_mult=9.0]  PF:2.26  WR:56.0%  Trades:50  DD:8.1%  AvgR:0.54
  APT (4h): 3 graduates
    (SHORT) E1: MACD Rollover + Death Cross [stop_atr_mult=1.5]  PF:3.04  WR:61.5%  Trades:13  DD:7.8%  AvgR:0.83
    (SHORT) E1: MACD Rollover + Death Cross [target2_atr_mult=3.0]  PF:2.93  WR:68.8%  Trades:16  DD:7.8%  AvgR:0.64
    (SHORT) E1: MACD Rollover + Death Cross [target2_atr_mult=4.5]  PF:2.65  WR:64.3%  Trades:14  DD:7.8%  AvgR:0.62
  ASTER (1h): 3 graduates
    E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]  PF:5.48  WR:63.6%  Trades:11  DD:4.0%  AvgR:1.68
    C1: OI Accumulation [stop_atr_mult=1.0]  PF:4.52  WR:60.0%  Trades:10  DD:4.0%  AvgR:1.50
    E9: OI Surge Standalone (ETH) [oi_surge_pct=2.5]  PF:2.75  WR:66.7%  Trades:36  DD:4.5%  AvgR:0.61
  ASTER (4h): 1 graduate
    (SHORT) E2: MACD Rollover + Crowd Long [target1_atr_mult=3.75]  PF:2.45  WR:58.3%  Trades:12  DD:5.9%  AvgR:0.58
  AVAX (1h): 2 graduates
    (SHORT) E5: Death Cross + Crowd Long [stop_atr_mult=1.5]  PF:4.46  WR:64.3%  Trades:28  DD:5.9%  AvgR:0.96
    (SHORT) E11: Triple Short (MACD + Death Cross + Crowd Long) [target1_atr_mult=4.5]  PF:2.78  WR:57.1%  Trades:14  DD:5.9%  AvgR:0.79
  AVAX (4h): 1 graduate
    (SHORT) E5: Death Cross + Crowd Long [stop_atr_mult=1.5]  PF:2.88  WR:60.0%  Trades:25  DD:5.9%  AvgR:0.80
  BNB (1h): 1 graduate
    E9: OI Surge Standalone (ETH) [stop_atr_mult=2.5]  PF:3.91  WR:71.4%  Trades:21  DD:2.8%  AvgR:0.67
  BNB (4h): 1 graduate
    (SHORT) E5: Death Cross + Crowd Long [ls_crowd_long=2.375]  PF:8.68  WR:86.7%  Trades:15  DD:2.0%  AvgR:0.99
  BTC (1h): 1 graduate
    (SHORT) E5: Death Cross + Crowd Long [ls_crowd_long=2.375]  PF:3.82  WR:70.0%  Trades:10  DD:2.0%  AvgR:0.88
  BTC (4h): 2 graduates
    (SHORT) E2: MACD Rollover + Crowd Long [target1_atr_mult=4.5]  PF:2.97  WR:57.1%  Trades:14  DD:7.6%  AvgR:0.78
    (SHORT) E1: MACD Rollover + Death Cross [target1_atr_mult=4.5]  PF:2.63  WR:56.2%  Trades:16  DD:5.9%  AvgR:0.71
  DOGE (1h): 2 graduates
    E9: OI Surge Standalone (ETH) [stop_atr_mult=1.5]  PF:2.96  WR:61.1%  Trades:18  DD:4.0%  AvgR:0.66
    (SHORT) E4: BB Upper + Crowd Long [ls_crowd_long=2.375]  PF:2.93  WR:66.7%  Trades:12  DD:4.0%  AvgR:0.62
  DOGE (4h): 2 graduates
    (SHORT) E11: Triple Short (MACD + Death Cross + Crowd Long) [ls_crowd_long=2.375]  PF:5.40  WR:75.0%  Trades:12  DD:2.0%  AvgR:1.18
    (SHORT) E4: BB Upper + Crowd Long [target1_atr_mult=3.75]  PF:2.25  WR:46.7%  Trades:15  DD:6.2%  AvgR:0.76
  ENA (1h): 2 graduates
    E7: OI Surge + BB Squeeze (ETH) [bb_squeeze_pct=0.3125]  PF:7.52  WR:77.8%  Trades:18  DD:4.0%  AvgR:1.37
    E9: OI Surge Standalone (ETH) [target2_atr_mult=7.5]  PF:5.00  WR:73.0%  Trades:37  DD:2.8%  AvgR:1.02
  ENA (4h): 5 graduates
    E7: OI Surge + BB Squeeze (ETH) [stop_atr_mult=1.12]  PF:4.76  WR:60.0%  Trades:10  DD:4.0%  AvgR:1.41
    (SHORT) E2: MACD Rollover + Crowd Long [target1_atr_mult=4.5]  PF:4.35  WR:70.0%  Trades:10  DD:5.9%  AvgR:1.03
    (SHORT) E11: Triple Short (MACD + Death Cross + Crowd Long) [target2_atr_mult=4.5]  PF:3.36  WR:60.0%  Trades:10  DD:4.0%  AvgR:0.95
    E9: OI Surge Standalone (ETH) [oi_surge_pct=3.0]  PF:3.43  WR:68.8%  Trades:16  DD:4.0%  AvgR:0.78
    (SHORT) E5: Death Cross + Crowd Long [target2_atr_mult=7.5]  PF:2.85  WR:66.7%  Trades:15  DD:5.9%  AvgR:0.61
  ENS (1h): 1 graduate
    (SHORT) E12: RSI OB Short + Death Cross (ETH) [target2_atr_mult=7.5]  PF:1.93  WR:50.0%  Trades:14  DD:4.0%  AvgR:0.50
  ENS (4h): 2 graduates
    (SHORT) E1: MACD Rollover + Death Cross [target2_atr_mult=3.0]  PF:3.15  WR:68.8%  Trades:16  DD:2.5%  AvgR:0.62
    (SHORT) C2: OI Distribution [target1_atr_mult=4.5]  PF:2.12  WR:50.0%  Trades:10  DD:4.0%  AvgR:0.62
  ETH (1h): 2 graduates
    E7: OI Surge + BB Squeeze (ETH) [stop_atr_mult=2.25]  PF:15.36  WR:91.7%  Trades:12  DD:2.0%  AvgR:1.22
    E9: OI Surge Standalone (ETH) [oi_surge_pct=3.0]  PF:3.13  WR:64.0%  Trades:25  DD:4.0%  AvgR:0.76
  ETH (4h): 1 graduate
    (SHORT) G12: MACD Bullish + ADX Strong (SHORT) [stop_atr_mult=1.5]  PF:3.17  WR:60.0%  Trades:15  DD:4.0%  AvgR:0.93
  FARTCOIN (1h): 4 graduates
    C1: OI Accumulation [stop_atr_mult=1.0]  PF:14.61  WR:81.8%  Trades:11  DD:2.0%  AvgR:2.47
    E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]  PF:14.49  WR:81.8%  Trades:11  DD:2.0%  AvgR:2.44
    E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]  PF:14.09  WR:81.8%  Trades:11  DD:2.0%  AvgR:2.37
    G8: Triple Energy Buildup [oi_surge_pct=3.75]  PF:3.77  WR:61.1%  Trades:18  DD:5.9%  AvgR:1.17
  FARTCOIN (4h): 1 graduate
    E9: OI Surge Standalone (ETH) [stop_atr_mult=1.5]  PF:3.33  WR:61.9%  Trades:21  DD:5.9%  AvgR:0.91
  FLOW (1h): 3 graduates
    E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]  PF:5.11  WR:70.0%  Trades:10  DD:4.0%  AvgR:1.34
    C1: OI Accumulation [stop_atr_mult=1.0]  PF:4.52  WR:70.0%  Trades:10  DD:4.0%  AvgR:1.15
    (SHORT) G12: MACD Bullish + ADX Strong (SHORT) [stop_atr_mult=1.0]  PF:3.20  WR:47.1%  Trades:17  DD:5.9%  AvgR:1.06
  FLOW (4h): 2 graduates
    (SHORT) E1: MACD Rollover + Death Cross [stop_atr_mult=1.0]  PF:3.42  WR:55.6%  Trades:18  DD:5.9%  AvgR:1.22
    (SHORT) G12: MACD Bullish + ADX Strong (SHORT) [adx_strong=12.5]  PF:5.66  WR:81.2%  Trades:16  DD:5.9%  AvgR:1.05
  HYPE (1h): 2 graduates
    E9: OI Surge Standalone (ETH) [stop_atr_mult=1.0]  PF:4.64  WR:60.0%  Trades:35  DD:7.8%  AvgR:1.31
    E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]  PF:3.40  WR:50.0%  Trades:10  DD:2.0%  AvgR:1.32
  JUP (4h): 1 graduate
    (SHORT) E1: MACD Rollover + Death Cross [target2_atr_mult=4.5]  PF:2.86  WR:69.2%  Trades:13  DD:2.5%  AvgR:0.64
  LINK (1h): 2 graduates
    C1: OI Accumulation [rsi_os=52.5]  PF:4.35  WR:73.7%  Trades:19  DD:7.8%  AvgR:0.98
    E10: OI Div Bullish + RSI Oversold (ETH) [rsi_os=52.5]  PF:4.48  WR:75.0%  Trades:20  DD:6.5%  AvgR:0.87
  LINK (4h): 3 graduates
    E7: OI Surge + BB Squeeze (ETH) [bb_squeeze_pct=0.125]  PF:7.87  WR:80.0%  Trades:10  DD:2.0%  AvgR:1.04
    (SHORT) B3: OI Breakout Short [stop_atr_mult=1.88]  PF:3.42  WR:70.0%  Trades:10  DD:2.7%  AvgR:0.74
    (SHORT) E5: Death Cross + Crowd Long  PF:3.20  WR:72.7%  Trades:22  DD:4.0%  AvgR:0.64
  PENDLE (1h): 1 graduate
    E7: OI Surge + BB Squeeze (ETH) [oi_surge_pct=3.0]  PF:4.77  WR:70.6%  Trades:17  DD:4.0%  AvgR:1.20
  PENDLE (4h): 2 graduates
    (SHORT) G12: MACD Bullish + ADX Strong (SHORT) [stop_atr_mult=1.0]  PF:2.81  WR:46.7%  Trades:15  DD:7.8%  AvgR:1.02
    E7: OI Surge + BB Squeeze (ETH) [oi_surge_pct=2.5]  PF:5.48  WR:80.0%  Trades:10  DD:2.0%  AvgR:0.98
  PUMP (1h): 3 graduates
    B2: OI Breakout Long [vol_surge=1.125]  PF:13.68  WR:90.0%  Trades:10  DD:2.0%  AvgR:1.53
    G8: Triple Energy Buildup [vol_surge=1.125]  PF:5.89  WR:75.0%  Trades:16  DD:4.0%  AvgR:1.24
    E7: OI Surge + BB Squeeze (ETH) [target1_atr_mult=3.75]  PF:3.01  WR:48.3%  Trades:29  DD:5.5%  AvgR:1.02
  PUMP (4h): 1 graduate
    (SHORT) C2: OI Distribution [target1_atr_mult=3.75]  PF:2.29  WR:57.1%  Trades:14  DD:7.9%  AvgR:0.57
  RENDER (4h): 2 graduates
    E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]  PF:4.29  WR:70.0%  Trades:10  DD:2.0%  AvgR:1.06
    E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]  PF:4.29  WR:70.0%  Trades:10  DD:2.0%  AvgR:1.06
  SKY (1h): 1 graduate
    E8: OI Surge + RSI Oversold (ETH) [oi_surge_pct=3.0]  PF:13.96  WR:91.7%  Trades:12  DD:2.0%  AvgR:1.28
  SKY (4h): 2 graduates
    E7: OI Surge + BB Squeeze (ETH) [stop_atr_mult=1.12]  PF:4.22  WR:60.0%  Trades:10  DD:2.0%  AvgR:1.28
    F6: Fear Oversold Bounce [target2_atr_mult=7.5]  PF:3.95  WR:70.0%  Trades:10  DD:4.0%  AvgR:0.84
  SKYAI (4h): 2 graduates
    E9: OI Surge Standalone (ETH) [stop_atr_mult=1.0]  PF:3.36  WR:56.8%  Trades:37  DD:4.0%  AvgR:1.14
    A4: Fear & Greed Extreme Fear Buy [fg_fear=15.0]  PF:6.19  WR:83.3%  Trades:12  DD:2.4%  AvgR:0.89
  SOL (1h): 2 graduates
    E8: OI Surge + RSI Oversold (ETH) [rsi_os=52.5]  PF:6.39  WR:76.2%  Trades:21  DD:2.8%  AvgR:1.15
    E9: OI Surge Standalone (ETH) [target1_atr_mult=4.5]  PF:3.46  WR:62.5%  Trades:32  DD:7.9%  AvgR:0.89
  SOL (4h): 1 graduate
    (SHORT) C2: OI Distribution [target1_atr_mult=4.5]  PF:2.56  WR:58.3%  Trades:12  DD:4.0%  AvgR:0.70
  SUI (4h): 2 graduates
    (SHORT) E5: Death Cross + Crowd Long [target1_atr_mult=3.75]  PF:3.53  WR:66.7%  Trades:12  DD:2.2%  AvgR:0.91
    (SHORT) G12: MACD Bullish + ADX Strong (SHORT) [stop_atr_mult=1.5]  PF:3.28  WR:66.7%  Trades:12  DD:2.0%  AvgR:0.79
  SYRUP (1h): 3 graduates
    E7: OI Surge + BB Squeeze (ETH) [bb_squeeze_pct=0.375]  PF:5.98  WR:75.0%  Trades:28  DD:2.0%  AvgR:1.28
    G8: Triple Energy Buildup [vol_surge=0.75]  PF:4.31  WR:68.4%  Trades:19  DD:4.0%  AvgR:1.10
    E9: OI Surge Standalone (ETH) [stop_atr_mult=1.5]  PF:2.39  WR:56.1%  Trades:66  DD:5.9%  AvgR:0.65
  TAO (1h): 2 graduates
    E9: OI Surge Standalone (ETH) [target1_atr_mult=4.5]  PF:3.42  WR:61.4%  Trades:57  DD:4.4%  AvgR:0.85
    E7: OI Surge + BB Squeeze (ETH) [stop_atr_mult=2.25]  PF:5.87  WR:78.6%  Trades:28  DD:2.0%  AvgR:0.82
  TAO (4h): 1 graduate
    E9: OI Surge Standalone (ETH) [target1_atr_mult=3.75]  PF:2.38  WR:60.0%  Trades:20  DD:5.9%  AvgR:0.50
  UNI (1h): 1 graduate
    E9: OI Surge Standalone (ETH) [stop_atr_mult=1.0]  PF:2.69  WR:50.0%  Trades:10  DD:7.8%  AvgR:1.01
  UNI (4h): 1 graduate
    E9: OI Surge Standalone (ETH) [target2_atr_mult=7.5]  PF:2.28  WR:61.1%  Trades:18  DD:4.5%  AvgR:0.53
  WLD (1h): 1 graduate
    E7: OI Surge + BB Squeeze (ETH) [target1_atr_mult=4.5]  PF:3.82  WR:64.3%  Trades:14  DD:4.0%  AvgR:1.05
  WLFI (1h): 1 graduate
    E7: OI Surge + BB Squeeze (ETH) [target1_atr_mult=3.75]  PF:3.62  WR:61.5%  Trades:13  DD:5.9%  AvgR:1.07
  XPL (1h): 5 graduates
    E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]  PF:11.04  WR:80.0%  Trades:10  DD:2.0%  AvgR:2.06
    E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]  PF:10.98  WR:80.0%  Trades:10  DD:2.0%  AvgR:2.04
    C1: OI Accumulation [stop_atr_mult=1.0]  PF:10.40  WR:80.0%  Trades:10  DD:2.0%  AvgR:1.93
    D1: Volatility Squeeze Breakout [bb_squeeze_pct=0.3]  PF:18.67  WR:91.7%  Trades:12  DD:2.0%  AvgR:1.57
    E7: OI Surge + BB Squeeze (ETH) [bb_squeeze_pct=0.375]  PF:4.23  WR:72.5%  Trades:40  DD:7.8%  AvgR:0.99
  XRP (1h): 2 graduates
    (SHORT) E2: MACD Rollover + Crowd Long [stop_atr_mult=1.5]  PF:3.34  WR:62.5%  Trades:16  DD:4.0%  AvgR:0.81
    E9: OI Surge Standalone (ETH) [oi_surge_pct=3.0]  PF:3.23  WR:57.1%  Trades:14  DD:3.3%  AvgR:0.73
  XRP (4h): 2 graduates
    (SHORT) E11: Triple Short (MACD + Death Cross + Crowd Long) [target2_atr_mult=7.5]  PF:3.62  WR:64.3%  Trades:14  DD:2.0%  AvgR:0.99
    (SHORT) E2: MACD Rollover + Crowd Long [target1_atr_mult=4.5]  PF:3.24  WR:66.7%  Trades:15  DD:5.5%  AvgR:0.86
  ZRO (1h): 1 graduate
    E9: OI Surge Standalone (ETH) [target2_atr_mult=9.0]  PF:3.71  WR:69.6%  Trades:46  DD:4.5%  AvgR:0.75
  ZRO (4h): 2 graduates
    F6: Fear Oversold Bounce [fg_fear=30.0]  PF:2.93  WR:57.1%  Trades:14  DD:4.0%  AvgR:0.75
    A4: Fear & Greed Extreme Fear Buy [target2_atr_mult=12.0]  PF:2.64  WR:63.6%  Trades:11  DD:4.0%  AvgR:0.59

  Symbols with 0 graduates: BCH

## 4. DEAD SCENARIOS (0 graduates)

  34 scenarios produced 0 graduates:

    A1: Crowded Long Fade  [ZERO TRADES — signal never fires]
    A2: Crowded Short Squeeze  [ZERO TRADES — signal never fires]
    A3: Long Liq Cascade Bounce  [ZERO TRADES — signal never fires]
    B1: ETF Inflow Momentum  [6 trades total, none meeting graduation criteria]
    C3: Smart Money Divergence  [ZERO TRADES — signal never fires]
    D2: Trend Mean Reversion Short  [ZERO TRADES — signal never fires]
    E6: MACD Rollover + OBV Divergence  [ZERO TRADES — signal never fires]
    F1: Oversold Bounce (Uptrend)  [7 trades total, none meeting graduation criteria]
    F2: Oversold Bounce (Any Regime)  [16 trades total, none meeting graduation criteria]
    F3: Overbought Fade (Downtrend)  [32 trades total, none meeting graduation criteria]
    F4: Accumulation Bounce  [6 trades total, none meeting graduation criteria]
    F5: Distribution Fade  [6 trades total, none meeting graduation criteria]
    F7: RSI Extreme Oversold Snap  [ZERO TRADES — signal never fires]
    F8: RSI Extreme Overbought Fade  [11 trades total, none meeting graduation criteria]
    G10: Smart Money Accumulation Dip  [ZERO TRADES — signal never fires]
    G11: MACD Bullish + Golden Cross  [35 trades total, none meeting graduation criteria]
    G12: MACD Bullish + ADX Strong  [6 trades total, none meeting graduation criteria]
    G1: Triple Buy (MACD + OBV + RSI)  [ZERO TRADES — signal never fires]
    G2: Momentum Continuation Long  [17 trades total, none meeting graduation criteria]
    G3: Quad Short (MACD + OBV + Trend + Crowd)  [ZERO TRADES — signal never fires]
    G4: Derivatives Distribution Short  [ZERO TRADES — signal never fires]
    G5: Derivatives Squeeze Long  [ZERO TRADES — signal never fires]
    G6: Compressed Breakout Bull  [23 trades total, none meeting graduation criteria]
    G9: Short Squeeze Exhaustion Fade  [ZERO TRADES — signal never fires]
    H1: Greed Top Short (Sentiment + RSI)  [ZERO TRADES — signal never fires]
    H2: Greed Distribution Short  [ZERO TRADES — signal never fires]
    H3: Double Contrarian Short (Greed + Crowd)  [40 trades total, none meeting graduation criteria]
    H4: Fear Accumulation Long  [15 trades total, none meeting graduation criteria]
    H5: Double Contrarian Long (Fear + Crowd)  [10 trades total, none meeting graduation criteria]
    H6: Greed Standalone Short  [41 trades total, none meeting graduation criteria]
    I1: Full Institutional Bull  [ZERO TRADES — signal never fires]
    I2: ETF Dip Buy  [ZERO TRADES — signal never fires]
    I3: Coinbase Momentum Long  [ZERO TRADES — signal never fires]
    I4: Coinbase Accumulation  [ZERO TRADES — signal never fires]

## 5. DERIVATIVES IMPACT SUMMARY

  Derivatives scenarios that GRADUATED: 5
    ✓ A4: Fear & Greed Extreme Fear Buy (2 symbol-timeframe combos)
    ✓ B2: OI Breakout Long (1 symbol-timeframe combos)
    ✓ B3: OI Breakout Short (1 symbol-timeframe combos)
    ✓ C1: OI Accumulation (5 symbol-timeframe combos)
    ✓ C2: OI Distribution (4 symbol-timeframe combos)

  Derivatives scenarios with trades but NO graduation: 0

  Derivatives scenarios still DEAD (0 trades): 14
    ✗ A1: Crowded Long Fade (0 trades)
    ✗ A2: Crowded Short Squeeze (0 trades)
    ✗ A3: Long Liq Cascade Bounce (0 trades)
    ✗ B1: ETF Inflow Momentum (6 trades, not graduating)
    ✗ C3: Smart Money Divergence (0 trades)
    ✗ G10: Smart Money Accumulation Dip (0 trades)
    ✗ G4: Derivatives Distribution Short (0 trades)
    ✗ G5: Derivatives Squeeze Long (0 trades)
    ✗ G9: Short Squeeze Exhaustion Fade (0 trades)
    ✗ H1: Greed Top Short (Sentiment + RSI) (0 trades)
    ✗ H2: Greed Distribution Short (0 trades)
    ✗ H3: Double Contrarian Short (Greed + Crowd) (40 trades, not graduating)
    ✗ H4: Fear Accumulation Long (15 trades, not graduating)
    ✗ H5: Double Contrarian Long (Fear + Crowd) (10 trades, not graduating)
    ✗ H6: Greed Standalone Short (41 trades, not graduating)
    ✗ I1: Full Institutional Bull (0 trades)
    ✗ I2: ETF Dip Buy (0 trades)
    ✗ I3: Coinbase Momentum Long (0 trades)
    ✗ I4: Coinbase Accumulation (0 trades)