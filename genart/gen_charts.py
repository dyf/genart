import os
import matplotlib.pyplot as plt
import numpy as np
import random
from random_words import RandomWords
import sklearn.datasets
import enum
import pandas as pd
import h5py 
from PIL import Image
from functools import partial
import tensorflow as tf

@enum.unique
class Chart(enum.Enum):
    BAR_H = 0
    BAR_V = 1
    STACKED_BAR_H = 2
    STACKED_BAR_V = 3
    LINE_H = 4
    LINE_V = 5
    SCATTER = 6
    SCATTER_COLOR = 7




CMAPS = [ 'viridis', 'plasma', 'inferno', 'magma', 'cividis', 
          'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
          'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
          'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn',
          'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink',
            'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
            'hot', 'afmhot', 'gist_heat', 'copper',
            'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
            'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic',
            'twilight', 'twilight_shifted', 'hsv',
            'Pastel1', 'Pastel2', 'Paired', 'Accent',
                        'Dark2', 'Set1', 'Set2', 'Set3',
                        'tab10', 'tab20', 'tab20b', 'tab20c',
                        'flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern',
            'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg',
            'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar']

MARKERS = [ ".",",","o","v","^","<",">","1","2","3","4","8","s","p","P","*","h","H","+","x","X","D","d","|","_",0,1,2,3,4,5,6,7,8,9,10,11]

LEGEND_LOCS = ['upper left', 'upper right', 'lower left', 'lower right' ]

FIGSIZE = (5.12,5.12)

def randu(N, max_range):
    r = np.random.uniform(low=max_range[0], high=max_range[1], size=2)
    r.sort()
    return np.random.uniform(low=r[0], high=r[1], size=N)

def gen_bar(orientation, max_bars=50, data_max_range=[-100,100], figsize=FIGSIZE):    
    categorical = np.random.random() < 0.5
    n_rows = random.randint(1, max_bars)
    
    horizontal = orientation == 'horizontal'
    barf = plt.barh if horizontal else plt.bar
    tickf = plt.yticks if horizontal else plt.xticks
    
    ticks = None
    if categorical:
        rw = RandomWords()
        ticks = rw.random_words(count=n_rows)

    fig, ax = plt.subplots(figsize=figsize)

    coords = range(n_rows) 

    color = np.random.random((1,3))  
    data = randu(n_rows, data_max_range)
    barf(coords, data, tick_label=ticks, color=color)
    
    if not horizontal and categorical:
        plt.xticks(rotation=90)

    plt.tight_layout()

def gen_stacked_bar(orientation, max_vars=5, max_bars=50, data_max_range=[0,100], figsize=FIGSIZE):    
    categorical = np.random.random() < 0.5
    n_rows = random.randint(1, max_bars)
    num_vars = random.randint(2, max_vars)

    labels = RandomWords().random_words(count=num_vars)
    
    horizontal = orientation == 'horizontal'
    barf = plt.barh if horizontal else plt.bar
    tickf = plt.yticks if horizontal else plt.xticks
    startk = 'left' if horizontal else 'bottom'

    ticks = None
    if categorical:
        rw = RandomWords()
        ticks = rw.random_words(count=n_rows)

         

    fig, ax = plt.subplots(figsize=figsize)

    coords = range(n_rows) 

    start = np.zeros(n_rows)
    for vi in range(num_vars):
        color = np.random.random((1,3))  

        data = randu(n_rows, data_max_range)
                
        barf(coords, data, tick_label=ticks, color=color, label=labels[vi], **{startk:start} )

        start += data
    
    if not horizontal and categorical:
        plt.xticks(rotation=90)

    plt.legend()
    plt.tight_layout()
    
def gen_scatter_color(max_rows_per_var=400, data_max_range=[-100,100], enc_size_p=0.5, enc_color_p=0.5, marker_max_size=200, figsize=FIGSIZE):
    encode_size = np.random.random() < 0.8
    
    fig, ax = plt.subplots(figsize=figsize)

    num_rows = random.randint(1, max_rows_per_var)
                
    cov = sklearn.datasets.make_spd_matrix(2) * (data_max_range[1]-data_max_range[0]) * 0.5
    mean = np.random.uniform(low=data_max_range[0], high=data_max_range[1], size=2)
    data = np.random.multivariate_normal(mean, cov, size=num_rows)

    marker = random.choice(MARKERS[:5])
        
    size=None
    if encode_size:
        size = np.random.random(num_rows) * marker_max_size            
        
    color = randu(num_rows, data_max_range)
    cmap = random.choice(CMAPS)            

    r = ax.scatter(data[:,0], data[:,1], marker=marker, s=size, c=color, cmap=cmap)

    plt.colorbar(r)

    plt.tight_layout()

def gen_scatter(max_rows_per_var=400, data_max_range=[-100,100], max_vars=5, marker_max_size=200, figsize=FIGSIZE):
    encode_size = np.random.random() < 0.8
    num_vars = random.randint(1, max_vars)    
    labels = RandomWords().random_words(count=num_vars)
    markers = random.sample(MARKERS[:num_vars], num_vars)

    fig, ax = plt.subplots(figsize=figsize)

    for vi in range(num_vars):
        num_rows = random.randint(1, max_rows_per_var)
                
        cov = sklearn.datasets.make_spd_matrix(2) * (data_max_range[1]-data_max_range[0]) * 0.5
        mean = np.random.uniform(low=data_max_range[0], high=data_max_range[1], size=2)
        data = np.random.multivariate_normal(mean, cov, size=num_rows)
        
        size = np.random.random() * marker_max_size if encode_size else None        
        color = np.random.random((1,3)) 

        r = ax.scatter(data[:,0], data[:,1], marker=markers[vi], s=size, c=color, label=labels[vi])    

    plt.legend()
    plt.tight_layout()

def gen_line(orientation, max_rows=200, max_vars=5, data_max_range=[-100,100], figsize=FIGSIZE):

    num_vars = random.randint(1, max_vars)    
    labels = RandomWords().random_words(count=num_vars)
    num_rows = random.randint(1, max_rows)
    
    cov = sklearn.datasets.make_spd_matrix(num_vars) * (data_max_range[1]-data_max_range[0]) * 0.5
    mean = np.random.uniform(low=data_max_range[0], high=data_max_range[1], size=num_vars)
    data = np.random.multivariate_normal(mean, cov, size=num_rows)

    modranges = np.random.uniform(low=data_max_range[0]/4, high=data_max_range[1]/4, size=num_vars)
    modranges = np.array([modranges, -modranges]).T
    mods = np.array([np.linspace(r[0],r[1],num_rows) for r in modranges]).T
    data += mods
    
    tr = np.random.uniform(low=data_max_range[0], high=data_max_range[1], size=2)
    tr.sort()
    t = np.linspace(tr[0], tr[1], num_rows)    

    fig, ax = plt.subplots(figsize=figsize)
    
    for vi in range(num_vars):
        if orientation == 'horizontal': 
            x,y = t, data[:,vi]
        elif orientation == 'vertical':
            y,x = t, data[:,vi]
        else:
            assert()

        color = np.random.random(3)
        ax.plot(x,y, c=color, label=labels[vi])    

    plt.legend()
    plt.tight_layout()

CHART_GENERATORS = {
    Chart.BAR_H: partial(gen_bar, orientation='horizontal'),
    Chart.BAR_V: partial(gen_bar, orientation='vertical'),
    Chart.STACKED_BAR_H: partial(gen_stacked_bar, orientation='horizontal'),
    Chart.STACKED_BAR_V: partial(gen_stacked_bar, orientation='vertical'),
    Chart.LINE_H: partial(gen_line, orientation='horizontal'),
    Chart.LINE_V: partial(gen_line, orientation='vertical'),
    Chart.SCATTER_COLOR: gen_scatter_color,
    Chart.SCATTER: gen_scatter
}

def gen_images(N, out_dir, out_h5):        
    out = []


    charts = random.choices(list(CHART_GENERATORS.keys()), k=N)    
    chart_types = [ c.value for c in charts ]    
    chart_types = tf.one_hot(chart_types, depth=len(CHART_GENERATORS))
    
    sizes = [ 512, 256, 128, 64, 32, 16, 8 ]

    with h5py.File(out_h5, 'w') as f:
        f.create_dataset('chart_types', data=chart_types)

        img_hs = [ f.create_dataset(f'chart_{s}', shape=(N,s,s,3), dtype='uint8') for s in sizes ]

        for i in range(N):
            if i % 10 == 0:
                print(i)

            chart = charts[i]
            CHART_GENERATORS[chart]()

            data = plt_to_array()
            
            for si, size in enumerate(sizes):
                size_data = data
                if si > 0:
                    size_data = np.array(Image.fromarray(data).resize((size,size)))
                
                img_hs[si][i,:,:,:] = size_data

            plt.close()

def plt_to_array(fig=None):
    if fig is None:
        fig = plt.gcf()
    fig.canvas.draw()    
    data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    return data

def random_multivariate_normal(num_rows, num_vars, max_range):
    cov = sklearn.datasets.make_spd_matrix(num_vars) * (max_range[1]-max_range[0]) * 0.5
    mean = np.random.uniform(low=max_range[0], high=max_range[1], size=num_vars)
    return np.random.multivariate_normal(mean, cov, size=num_rows)


def gen_basic_bars(N, file_name, data_max_range=[-1000, 1000], max_vars=6, max_rows=10000, num_bins=10):
    data_range = np.sort(np.random.uniform(low=data_max_range[0], high=data_max_range[1], size=2))

    out_x = np.zeros((N, num_bins))
    out_y = np.zeros((N, num_bins))
    out_ori = np.random.randint(low=0, high=2, size=N).astype(np.uint8)
    out_color = np.random.random((N,3))

    ori_lookup = {
        0: 'horizontal',
        1: 'vertical'
    }
    
    with h5py.File(file_name, 'w') as hf:
        hf.create_dataset('ori', data=out_ori)
        hf.create_dataset('color', data=out_color)

        out_x = hf.create_dataset('x', shape=(N, num_bins), dtype='float32')
        out_y = hf.create_dataset('y', shape=(N, num_bins), dtype='float32')        
        out_img = hf.create_dataset('chart', shape=(N, 256, 256, 3), dtype='uint8')

        for ii in range(N):
            if ii % 100 == 0:
                print(f'{ii+1}/{N}')
            num_vars = np.random.randint(low=1, high=max_vars+1)
            num_rows = np.random.randint(low=1, high=max_rows+1)

            data = random_multivariate_normal(num_rows, num_vars, data_range)
            
            fig, ax = plt.subplots(figsize=(2.56,2.56))
            counts, bins, _ = ax.hist(data.flat, orientation=ori_lookup[out_ori[ii]], color=out_color[ii])
            plt.tight_layout()
            img = plt_to_array(fig)            
            plt.close()
            
            out_y[ii] = counts
            out_x[ii] = [ (bins[bi]+bins[bi+1])*0.5 for bi in range(len(bins)-1) ]
            out_img[ii] = 255 
            out_img[ii,:img.shape[0],:img.shape[1],:] = img


def gen_basic_bars_async(args):    
    i, n, fname = args    
    print(i, n,fname)
    np.random.seed(i)
    gen_basic_bars(n, fname)

if __name__ == "__main__":

    import multiprocessing as mp

    runs = [
        [ 0, 1000, 'data/charts/bars_test_000.h5' ]
    ] + [ 
        [ (i+1)*1238746, 1000, f'data/charts/bars_train_{i:03}.h5'] for i in range(100) 
    ]
        

    with mp.Pool(10) as p:
        p.map(gen_basic_bars_async, runs)

    
    #gen_basic_bars(100000, 'data/charts/bars_train.h5')
    #gen_images(1000, "data/charts", "data/charts/charts_test.h5")
    #gen_stacked_bar(orientation='horizontal', categorical=False)    
    #gen_scatter()
    #gen_line(orientation='vertical')    
    

    


