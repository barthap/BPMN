from typing import Dict

from import_handler import Result
def calculate_significance_dependency_matrix(import_result: Result):
    significance_dependency = dict()
    for event, counter in import_result.direct_succession.items():
        significance_dependency[event] = dict()
        for successor_name, successor_count in counter.most_common():
            try:
                t21 = import_result.direct_succession[successor_name][event]
            except KeyError:
                t21 = 0
            t12 = import_result.direct_succession[event][successor_name]
            significance_dependency[event][successor_name] = (t12 - t21)/ (t12 + t21 +1)

    return significance_dependency

def calculate_2loop_matrix(import_result: Result):
    two_loop = dict()
    for event, counter in import_result.direct_succession.items():
        for successor_name, successor_count in counter.most_common():
            if successor_name != event:
                counter_now = 0
                substring = ';'.join([event, successor_name, event])
                for trace in import_result.traces_df.iterrows():
                    activity_str = trace[1]['Activity']
                    counter_now += activity_str[:-1].count(substring)
                if counter_now != 0:
                    if event in two_loop:
                        two_loop[event][successor_name] = counter_now
                    else:
                        two_loop[event] = dict([(successor_name, counter_now)])

    two_loop_significance = dict()
    for outside, outside_dict in two_loop.items():
        for inside, count in outside_dict.items():
            t12 = count
            try:
                t21 = two_loop[inside][outside]
            except KeyError:
                t21 = 0

            value = (t12 + t21)/(t12 + t21 +1)
            try:
                if inside not in two_loop_significance[outside] and outside not in two_loop_significance[inside]:
                    two_loop_significance[outside][inside] = value
            except KeyError:
                if outside in two_loop_significance:
                    two_loop_significance[outside][inside] = value
                else:
                    two_loop_significance[outside] = dict([(inside, value)])

    return  two_loop_significance



def filter_network_by_matrices(sd_dict: Dict[str, Dict[str, float]], two_loop_dict: Dict[str, Dict[str, float]], threshold: float):
    filtered_direct_succession = dict()
    filtered_out_two_loop = dict()
    parallel_tuples = []
    self_loop_events = []


    for eventA , dictA in sd_dict.items():
        for eventB, value in dictA.items():
            if eventB == eventA:
                self_loop_events.append(eventB)

            if threshold <= value:
                if eventA in filtered_direct_succession:
                    filtered_direct_succession[eventA][eventB] = value
                else:
                    filtered_direct_succession[eventA] = dict([(eventB, value)])

            try:
                if abs(sd_dict[eventB][eventA]) >= threshold and abs(sd_dict[eventA][eventB]) >= threshold:
                    parallel_tuples.append((eventA, eventB))
            except KeyError:
                pass


    for out_loop , dict_out in two_loop_dict.items():
        for in_loop, value in dict_out.items():
            if value >= threshold:
                if out_loop in filtered_out_two_loop:
                    filtered_out_two_loop[out_loop][in_loop] = value
                else:
                    filtered_out_two_loop[out_loop] = dict([(in_loop, value)])

    return filtered_direct_succession, filtered_out_two_loop, parallel_tuples, self_loop_events