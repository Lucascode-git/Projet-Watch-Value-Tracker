# 1: Imports
from numpy import std
import pandas as pd
import matplotlib.pyplot as plt 
import numpy as np


from app import get_history, compute_stats

stats = compute_stats(get_history('rolex-daytona-126500ln'))

assert stats['current_price'] == 28250
assert stats['change_12m'] == -4.4
assert stats['change_total'] == -27.8
assert stats['premium'] == 76.6
assert stats['yearly_volatility'] == 9.0
print('All checks passed')
