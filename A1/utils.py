from numpy import random
import numpy as np
import random


def generate_exponential(mean):
    t = random.exponential(scale = mean)
    return t

def generate_uniform(lo,hi):
    return np.random.uniform(lo,hi)

def select_random(l):
    return random.choice(l)
