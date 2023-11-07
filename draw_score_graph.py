# unpickle the score data and draw the graph

import pickle
import matplotlib.pyplot as plt
import numpy as np

file_name_list = [ 'score_DRQN-Stack.pkl', 'score_DRQN-Store-State.pkl', 'score_R2D2.pkl']

def main():
    score_list_dict = {}
    for file_name in file_name_list:
        with open(file_name, 'rb') as f:
            score_list_dict[file_name] = pickle.load(f)
    
    # print(score_list)
    for file_name in file_name_list:
        plt.plot(np.arange(len(score_list_dict[file_name])), score_list_dict[file_name], label=file_name[:-4])
        plt.xlabel('Episode')
        plt.ylabel('Score')
        plt.legend()
    plt.show()
    
if __name__=="__main__":
    main()
    
