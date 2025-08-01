# Trade Engine Service

Python 0X Lଘ �t) ��<\, 1L�� |t �t)D �P ��i��.

## =� �� 0�

- **� 1L�**: vectorbtpro| \�\ �1� 1L�
- **|t �t)**: IBKR API| �\ �� �� p�
- **�\ � ��**: ��T � ��l
- **��l  �**: ��X l0 p  �/u  �
- **pt0  �**: ����� pt0 �  �� ���

## =� 0  ��

- Python 3.11+
- ib_insync (IBKR API)
- vectorbtpro (1L�)
- pandas, numpy (pt0 ��)
- SQLite (\� pt0  �)
- ta-lib (0  �\)

## =� $  �

### � �l�m

- Python 3.11 t�
- IBKR TWS/Gateway � 
- TA-Lib $X (��� $X )� �t)

### X� $

1.  �X� �1  \1T:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Xt1 $X:
```bash
pip install -r requirements.txt
```

3. X� � $:
- Windows: `.env_dev` | �� ��
- Linux: `.env_prod` | �� ��
- D�� t� | 

### �

```bash
# Tx `� tX �
python main.py

# � �<\ 1L�
python src/order/runner.py
```

## =� \� lp

```
src/
   data/            # pt0 �5
      data_loader.py      # IBKR pt0 \T
      connect_IBKR.py     # IBKR �  �
      resampler.py        # pt0 ���
   strategies/      # � l
      base_strategy.py    # � �t� t��
      example*.py         #  ��
   order/           # �8  �
      order_manager.py    # �8 �  �
      broker_IBKR.py      # IBKR \� l
      runner.py           # 1L� �
   infra/           # x|���
      sqlite/             # pt0�t�
   config.py        # $  �
   trade.py         # Tx �t� t��
```

## =' �� ���

### Trade Engine (trade.py)
- 1L�/|t �� X
- � � $ ��tX
- IBKR �  �

### Data Layer
- **IBKRData**: ����� pt0 �\�  �� ���
- **Resampler**: �\ ���<\ pt0 �X

### Strategy Framework
- **BaseStrategy**: �� �X �� �t� t��
- �� �1  ��X  � \� �h

### Order Management
- **OrderManager**: ��D � �8<\ �X
- **BrokerIBKR**: IBKR �T �8 �

## >� L��

```bash
# L�� � (L�� ��l $ D�)
python -m pytest tests/
```

## � $ 5X

`config.py`�  �� �� $:
- `TRADE_MODE`: "back" (1L�) � "live" (�p�)
- `TRADE_REAL`: "paper" (�X) � "live" (�p�)
- `IBKR_PORT`: 4002 (paper) � 4001 (live)

## � �X�m

- IBKR � � � \ Client ID �� (0�: 20)
- Paper Trading<\ ��� L�� � �p� ĉ
- �� pt0� \1 0<\ ��(
-  � ����� pt0 �� � IBKR \ Ux

## >  ( D�

- [Trade Batch](../trade_batch/README.md) - 0X �� D�
- [Trade Dashboard](../trade_dashboard/README.md) -  ��� 1��
- [Trade Frontend](../trade_frontend/README.md) - � x0�t�