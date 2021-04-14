import pandas as pd
from more_itertools import pairwise
from collections import Counter
from typing import Set, Dict

class Result:
    def __init__(self, direct_succession: Dict[str, Counter],
                 start_events: Set[str],
                 end_events: Set[str]):
        self.end_events = end_events
        self.start_events = start_events
        self.direct_succession = direct_succession


class CsvResult(Result):
    def __init__(self,
                 direct_succession: Dict[str, Counter],
                 event_counter: Dict[str, int],
                 start_events: Set[str],
                 end_events: Set[str]):
        super(CsvResult, self).__init__(direct_succession,start_events,end_events)
        self.event_counter = event_counter


def from_csv(filename: str, sep=",") -> CsvResult:
    df = pd.read_csv(filename, sep=sep)
    try:
        df['Start Event'] = pd.to_datetime(df['Start Timestamp'])
        df['End Event'] = pd.to_datetime(df['Complete Timestamp'])
        dfs = df[['Case ID', 'Activity', 'Start Event']]
    except Exception:
        df['start'] = pd.to_datetime(df['datetime'])
        dfs = df[['id', 'activity', 'start']]
        dfs = dfs.rename(columns = {'id': 'Case ID', 'activity': 'Activity', 'start': 'Start Event'}, inplace = False)


    ev_counter = dfs.groupby(['Activity']).Activity.count()

    dfs = dfs.sort_values(by=['Case ID','Start Event'])\
      .groupby(['Case ID'])\
      .agg({'Activity': ';'.join})

    dfs['Count'] = 0
    dfs = dfs.groupby('Activity', as_index=False).count()\
      .sort_values(['Count'], ascending=False)\
      .reset_index(drop=True)

    dfs['Trace'] = [trace.split(';') for trace in dfs['Activity']]

    w_net = dict()
    ev_start_set = set()
    ev_end_set = set()
    for index, row in dfs[['Trace','Count']].iterrows():
        if row['Trace'][0] not in ev_start_set:
          ev_start_set.add(row['Trace'][0])
        if row['Trace'][-1] not in ev_end_set:
          ev_end_set.add(row['Trace'][-1])
        for ev_i, ev_j in pairwise(row['Trace']):
          if ev_i not in w_net.keys():
            w_net[ev_i] = Counter()
          w_net[ev_i][ev_j] += row['Count']

    return CsvResult(w_net, ev_counter, ev_start_set, ev_end_set)

from opyenxes.data_in.XUniversalParser import XUniversalParser
import more_itertools as itt

class XesImport(Result):
    def __init__(self,
                 traces: pd.DataFrame,
                 direct_succession: Dict[str, Counter],
                 start_events: Set[str],
                 end_events: Set[str]):
        super(XesImport, self).__init__(direct_succession, start_events, end_events)
        self.traces_df = traces

def from_xes(filename: str) -> XesImport:
    with open(filename) as log_file:
        log = XUniversalParser().parse(log_file)[0]

    traceTable = []
    for trace in log:
        traceString = ""
        for event in trace:
            if event.get_attributes()['lifecycle:transition'].get_value() == "start":
                traceString = traceString + event.get_attributes()['Activity'].get_value() + ";"
        traceTable.append(traceString[:-1])
    uniqueTraces = list(set(traceTable))
    pandasImport = []
    idx = 0

    for uniqueTrace in uniqueTraces:
      pandasImport.append({"idx": idx, "trace":uniqueTrace, 'count': traceTable.count(uniqueTrace)})
      idx+=1

    df = pd.DataFrame(pandasImport).set_index("idx").sort_values(['count'], ascending=False) \
        .reset_index(drop=True)

    w_net = dict()
    ev_start_set = set()
    ev_end_set = set()
    for index, row in df[['trace', 'count']].iterrows():
        if row['trace'][0] not in ev_start_set:
            ev_start_set.add(row['trace'][0])
        if row['trace'][-1] not in ev_end_set:
            ev_end_set.add(row['trace'][-1])
        for ev_i, ev_j in itt.pairwise(row['trace']):
            if ev_i not in w_net.keys():
                w_net[ev_i] = Counter()
            w_net[ev_i][ev_j] += row['count']

    return XesImport(df, w_net, ev_start_set, ev_end_set)

def import_handler(filename: str, sep=',') -> Result:
    if filename.endswith("csv"):
        return from_csv(filename, sep)
    elif filename.endswith("xes"):
        return from_xes(filename)