import pandas as pd
from opyenxes.data_in.XUniversalParser import XUniversalParser
import more_itertools as itt
from collections import Counter
from typing import Set, Dict

class XesImport:
    def __init__(self,
                 traces: pd.DataFrame,
                 direct_succession: Dict[str, Counter],
                 start_events: Set[str],
                 end_events: Set[str]):
        self.traces_df = traces
        self.direct_succession = direct_succession
        self.start_events = start_events
        self.end_events = end_events

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


