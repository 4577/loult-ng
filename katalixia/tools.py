from random import uniform


def weighted_choice(choices, weights):
    uniform_sample = uniform(0, sum(weights))
    weights_sum = 0
    for i, weight in enumerate(weights):
        updated_weight_sum = weights_sum + weight # to prevent computing weight_sum + weight twice
        if updated_weight_sum > uniform_sample:
            return choices[i]
        else:
            weights_sum = updated_weight_sum
