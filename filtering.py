from typing import Dict

from import_handler import Result
def calculate_significance_dependency_matrix(import_result: Result):
    significance_dependency = dict()
    for event, counter in import_result.direct_succession.items():
        significance_dependency[event] = dict()
        for successor_name, successor_count in counter.most_common():
            try:
                t21 = significance_dependency[successor_name][event]
            except KeyError:
                t21 = 0
            t12 = significance_dependency[event][successor_count]
            significance_dependency[event][successor_name] = (t12 - t21)/ (t12 + t21 +1)

    return significance_dependency

def calculate_2loop_matrix(import_result: Result):
    two_loop = dict()
    for event, counter in import_result.direct_succession.items():
        for successor_name, successor_count in counter.most_common():
            counter = 0
            for trace in import_result.traces_df.iterrows():
                counter += trace.count(';'.join([event, successor_name, event])[:-1])
            if counter != 0:
                if two_loop[event]:
                    two_loop[event][successor_name] = counter
                else:
                    two_loop[event] = dict([(successor_name, counter)])

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
                if two_loop_significance[outside]:
                    two_loop_significance[outside] = value
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
            if value == 0:
                parallel_tuples.append((eventA, eventB))

            if threshold <= value:
                if filtered_direct_succession[eventA]:
                    filtered_direct_succession[eventA][eventB] = value
                else:
                    filtered_direct_succession[eventA] = dict([(eventB, value)])

    for out_loop , dict_out in two_loop_dict.items():
        for in_loop, value in dict_out.items():
            if value >= threshold:
                if filtered_out_two_loop[out_loop]:
                    filtered_out_two_loop[out_loop][in_loop] = value
                else:
                    filtered_out_two_loop[out_loop] = dict([(in_loop, value)])

    return filtered_direct_succession, filtered_out_two_loop, parallel_tuples, self_loop_events