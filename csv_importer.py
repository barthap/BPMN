from collections import Counter
from typing import Dict, Set
from more_itertools import pairwise

import pandas as pd

class CsvResult:
    def __init__(self,
                 direct_succession: Dict[str, Counter],
                 event_counter: Dict[str, int],
                 start_events: Set[str],
                 end_events: Set[str]):
        self.end_events = end_events
        self.start_events = start_events
        self.event_counter = event_counter
        self.direct_succession = direct_succession


def from_csv(filename: str) -> CsvResult:
    df = pd.read_csv(filename)
    df['start'] = pd.to_datetime(df['Start Timestamp'])
    df['end'] = pd.to_datetime(df['Complete Timestamp'])

    dfs = df[['Case ID', 'Activity', 'start']]

    ev_counter = dfs.groupby(['Activity']).Activity.count()

    dfs = dfs.sort_values(by=['Case ID','start'])\
      .groupby(['Case ID'])\
      .agg({'Activity': ';'.join})

    dfs['count'] = 0
    dfs = dfs.groupby('Activity', as_index=False).count()\
      .sort_values(['count'], ascending=False)\
      .reset_index(drop=True)

    dfs['trace'] = [trace.split(';') for trace in dfs['Activity']]

    w_net = dict()
    ev_start_set = set()
    ev_end_set = set()
    for index, row in dfs[['trace','count']].iterrows():
        if row['trace'][0] not in ev_start_set:
          ev_start_set.add(row['trace'][0])
        if row['trace'][-1] not in ev_end_set:
          ev_end_set.add(row['trace'][-1])
        for ev_i, ev_j in pairwise(row['trace']):
          if ev_i not in w_net.keys():
            w_net[ev_i] = Counter()
          w_net[ev_i][ev_j] += row['count']

    return CsvResult(w_net, ev_counter, ev_start_set, ev_end_set)
