import os
import sys
import gym
import random
import numpy as np

import torch
import torch.optim as optim
import torch.nn.functional as F
from model import DRQN
from memory import Memory
from tensorboardX import SummaryWriter
import pickle
from config import env_name, initial_exploration, batch_size, update_target, goal_score, log_interval, device, replay_memory_capacity, lr, sequence_length

from collections import deque

def get_action(state, target_net, epsilon, env, hidden):
    action, hidden = target_net.get_action(state, hidden)
    
    if np.random.rand() <= epsilon:
        return env.action_space.sample(), hidden
    else:
        return action, hidden

def update_target_model(online_net, target_net):
    # Target <- Net
    target_net.load_state_dict(online_net.state_dict())

def state_to_partial_observability(state):
    try:
        state = state[0][[0,2]]
    except IndexError:
        state = np.array(state)[[0,2]]
    return state


def main():
    env = gym.make(env_name)
    torch.manual_seed(500)

    # num_inputs = env.observation_space.shape[0]
    num_inputs = 2
    num_actions = env.action_space.n
    print('state size:', num_inputs)
    print('action size:', num_actions)

    online_net = DRQN(num_inputs, num_actions)
    target_net = DRQN(num_inputs, num_actions)
    update_target_model(online_net, target_net)

    optimizer = optim.Adam(online_net.parameters(), lr=lr)
    writer = SummaryWriter('logs')

    online_net.to(device)
    target_net.to(device)
    online_net.train()
    target_net.train()
    memory = Memory(replay_memory_capacity)
    running_score = 0
    epsilon = 1.0
    steps = 0
    loss = 0

    score_list = []
    
    for e in range(30000):
        done = False

        score = 0
        state = env.reset(seed=500)
        state = state_to_partial_observability(state)
        state = torch.Tensor(state).to(device)

        hidden = (torch.Tensor().new_zeros(1, 1, 16), torch.Tensor().new_zeros(1, 1, 16))

        while not done:
            steps += 1

            action, new_hidden = get_action(state, target_net, epsilon, env, hidden)
            next_state, reward, done, _, _ = env.step(action)

            next_state = state_to_partial_observability(next_state)
            next_state = torch.Tensor(next_state)

            mask = 0 if done else 1
            reward = reward if not done or score == 499 else -1

            memory.push(state, next_state, action, reward, mask, hidden)
            hidden = new_hidden

            score += reward
            state = next_state

            
            if steps > initial_exploration and len(memory) > batch_size:
                epsilon -= 0.00005
                epsilon = max(epsilon, 0.1)

                batch = memory.sample(batch_size)
                loss = DRQN.train_model(online_net, target_net, optimizer, batch)

                if steps % update_target == 0:
                    update_target_model(online_net, target_net)

        score = score if score == 500.0 else score + 1
        if running_score == 0:
            running_score = score
        else:
            running_score = 0.99 * running_score + 0.01 * score
        score_list.append(running_score)
        if e % log_interval == 0:
            print('{} episode | score: {:.2f} | epsilon: {:.2f}'.format(
                e, running_score, epsilon))
            writer.add_scalar('log/score', float(running_score), e)
            writer.add_scalar('log/loss', float(loss), e)

        if running_score > goal_score:
            with open("score_DRQN-Store-State.pkl", "wb") as fp:
                pickle.dump(score_list, fp)
            break


if __name__=="__main__":
    main()
