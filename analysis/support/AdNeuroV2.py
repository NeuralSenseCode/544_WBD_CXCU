import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import scipy.signal as signal
import numpy as np
import pickle
import sys, os
import shutil
import matplotlib.pyplot as plt
from scipy.stats import norm
from neurallib import clean as clean
from neurallib import plot as plots
from neurallib.stats import get_significance, get_significance_footnote

#in_folder = f'../infiles/AdRawAll/'
#out_folder=f'../outfiles/Sandbox/'
#results_folder=f'../results/Sandbox/'

client = 'AdNeuro'
project = 'WB'

results_folder = f"../results/{project}/"
in_folder = f"../infiles/{project}/Sensors/"


out_folder = f"../outfiles/{project}/"
annotation_path = f"../ENE/AdNeuro/Individual Annotation Data.csv"

try:
    import msvcrt
    def get_key(z):
        print()
        print('-- Exception Raised --')
        print(f'>> Warning due to {z}')
        print('-- Press any key to continue...--')
        #msvcrt.getch()
        print()
except:
    pass


def get_files(folder, tags=['',]):
    return [f for f in os.listdir(folder) if not f.startswith('.') and all(x in f for x in tags)] 


class Advertisement:
    def __init__(self,name):
        self.name = name
        
        cols = ['ID','Time','Value']
        self.signals = {'Frontal Asymmetry Alpha':pd.DataFrame(columns= cols),
                       'High Engagement':pd.DataFrame(columns= cols),
                        'Low Engagement':pd.DataFrame(columns= cols),
                        'Distraction':pd.DataFrame(columns= cols),
                        'Drowsy':pd.DataFrame(columns= cols),
                       'Workload Average':pd.DataFrame(columns= cols)}
        
        self.averages = {'Frontal Asymmetry Alpha':pd.DataFrame(columns= cols),
                       'High Engagement':pd.DataFrame(columns= cols),
                        'Low Engagement':pd.DataFrame(columns= cols),
                        'Distraction':pd.DataFrame(columns= cols),
                        'Drowsy':pd.DataFrame(columns= cols),
                       'Low Workload':pd.DataFrame(columns= cols),
                        'Optimal Workload':pd.DataFrame(columns= cols),
                        'Overworked':pd.DataFrame(columns= cols),
                        'Workload Average':pd.DataFrame(columns= cols)}
        
        #self.moments = pd.DataFrame(columns=['Moment','Start','End'])
        
        cols = ['Moment','Start','End','Duration',
                'Frontal Asymmetry Alpha',
                'High Engagement',
                'Optimal Workload',
                'Low Workload',
                'Overworked',
                'Low Engagement',
                'Distraction',
                'Drowsy',
                'Workload Average',]
        
        self.moments = pd.DataFrame(columns = cols)
        self.moments['Moment']=['Whole',]
        self.moments['Start']=[0,]
        self.moments['End']=[0,]


    def update(self):
        pass

    
def update_ad(self):
    pass


def header(text):
    print("-"*len(text))
    print(text)
    print("-"*len(text))
  
    
def print_status(text, item):
    print(f">>>>> {text} : {item}")


def print_step(text, item):
    print(f">>> {text} : {item}")
 
    
def backup_files(results_folder):
    '''
    Saves the new pickle to the output folder
    '''
    path = f"{results_folder}"

    backups = ['Results']
    for b in backups:
        print_step('Backing Up',b)
        try:
            df = pd.read_csv(f'{path}{b}.csv')
            df.to_csv(f'{path}{b}_Backup.csv', index=False)
        except:
            print_status('Nothing to back up',b)
 
            
def remove(folder):  
    header("> Now Running: Cleanup Trash ")
    if os.path.exists(folder):
        try:
            shutil.rmtree(folder)
            print(f"> Removed Results: {folder}")
        except OSError as error:
            print(f"> ##### Error cleaning outfile directory: {error} ##### ")
 
            
def empty_trash():
    remove(results_folder)
    remove(out_folder)
    os.makedirs(results_folder, exist_ok=True)
    os.makedirs(out_folder, exist_ok=True) 

    
def clean_raw(data):
    data = data.replace(to_replace=-99999,value=np.nan)
    data = data.replace(to_replace=' ',value=np.nan)
    data = data.dropna()
    return data


def get_pickle(path, stimulus=None):
    try:
        with open(f"{path}{stimulus}.pickle", 'rb') as f:
            Ad = pickle.load(f)
            #print_status('Loaded',Ad.name)      
    except Exception as z:      
        if stimulus is not None:
            Ad=Advertisement(stimulus)
            #print_status('Created',Ad.name)
        else:
            print_status('Failed',f"{path} - {z!r}")
            return
    return Ad


def save_pickle(Ad, path):
    ### Save Pickle
    status = 'Failed'
    try:
        with open(f"{path}{Ad.name}.pickle", 'wb') as f:
                pickle.dump(Ad, f, pickle.HIGHEST_PROTOCOL)
        status = f'Saved to {path}{Ad.name}.pickle'
    except:
        status = 'Failed'      
    return status


def read_imotions(path):
    file = open(path, 'r')
    count = 0
    while True:
        line = file.readline()
        if '#' in line.split(',')[0]:
            count += 1
        else:
            break
    file.close()
    return pd.read_csv(path, index_col='Row', header=count, low_memory=False)


def butter_lowpass_filter(data, cutoff, fs, order=2):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = signal.filtfilt(b, a, data,method="pad")
    return y


def butter_highpass_filter(data, cutoff, fs, order=2):
    b, a = butter_highpass(cutoff, fs, order=order)
    y = signal.filtfilt(b, a, data,method="pad")
    return y


def butter_bandpass_filter(data, cutoffs, fs, order=2):
    b, a = butter_bandpass(cutoffs, fs, order=order)
    y = signal.filtfilt(b, a, data,method="pad")
    return y


def butter_lowpass(cutoff, fs, order=2):
    return signal.butter(order, cutoff, fs=fs, btype='low', analog=False)


def butter_highpass(cutoff, fs, order=2):
    return signal.butter(order, cutoff, fs=fs, btype='high', analog=False)


def butter_bandpass(cutoffs, fs, order=2):
    return signal.butter(order, cutoffs, fs=fs, btype='band', analog=False)


def add_raw_data(Ad, respondent,raw):
    ## For each metric
    start_time = raw.loc[raw['SlideEvent']=='StartMedia']['Timestamp'].values[0]
    end_time = raw.loc[raw['SlideEvent']=='EndMedia']['Timestamp'].values[0]
    dur = end_time-start_time
    
    raw = raw.loc[(raw['Timestamp']>=start_time)&(raw['Timestamp']<=end_time)]
    raw.loc[:,'Time']= raw['Timestamp']-start_time
    
    metrics = {'Frontal Asymmetry Alpha':128,
                      'High Engagement':256,
                      'Low Engagement':256,
                      'Distraction':256,
                      'Drowsy':256,
                      'Workload Average':256}
    
    for key,value in metrics.items():
        data = pd.DataFrame()
        uid = respondent + '_' + str(raw['Timestamp'].values[0])
        
        if uid not in Ad.signals[key]['ID'].tolist(): # 
            ### Correct Time
            
            if (key in raw.columns) and (len(raw[key].dropna())):
                data = raw[['Time',key]].dropna()
                data = clean_raw(data)
                if len(data):
                    if key == 'Frontal Asymmetry Alpha':
                        data.loc[:,'Time']=np.round((data['Time']/1000)*2)/2
                    else:
                        data.loc[:,'Time']=np.round((data['Time']/1000))

                        #data['Time'] = pd.to_datetime(data['Time'], unit='s')

                        ## Find the offset from the start of the second
                        #offsets = data['Time'] - data['Time'].dt.floor('s')

                        ## Subtract off the offset to round down
                        #data['Time'] = data['Time'] - offsets

                        ## Subtract the first timestamp to make the first one 0
                        #data['Time'] = data['Time'] - data['Time'].iloc[0]

                        ## Convert the 'Time' back to seconds from timedelta
                        #data['Time'] = data['Time'].dt.total_seconds()/1000

                    data.loc[:, 'ID']=uid
                    data = data.rename(columns={key:'Value'})
                    cols = ['ID','Time','Value']
                    data = data[cols]

                    Ad.signals[key]=pd.concat([Ad.signals[key],data])

                    print_status('Updated',key)
                else:
                    print_status('No Clean Data',key)
            else:
                print_status('Missing',key)
            
        else:
            print_status('Found',key)
        
    return Ad


def add_moments(Ad,raw):
    ###Check if data contains scene info
    if any(i for i in raw.columns if Ad.name in i):
        ###Check if data contains any new scene info
        moments = [i.split(' ')[0] for i in raw.columns if Ad.name in i]
        existing = Ad.moments['Moment'].tolist()
        if any(i for i in moments if i not in Ad.moments['Moment'].tolist()):
            start_time = raw.loc[raw['SlideEvent']=='StartMedia']['Timestamp'].values[0]
            end_time = raw.loc[raw['SlideEvent']=='EndMedia']['Timestamp'].values[0]
            dur = end_time-start_time
            raw = raw.loc[(raw['Timestamp']>=start_time)&(raw['Timestamp']<=end_time)]
            raw.loc[:,'Time']= raw['Timestamp']-start_time
            
            new_moments = [i for i in raw.columns if Ad.name in i]
            for new_moment in new_moments:
                title = new_moment.split(' ')[0]
                
                if title not in Ad.moments['Moment'].tolist():
                    data = raw.dropna(subset=new_moment)
                    times = data.dropna(subset=[new_moment])['Time'].values/1000
                    result = pd.DataFrame()
                    result['Moment']=[title]
                    result['Start']=[times[0]]
                    result['End']=[times[-1]]
                    result['Duration']=[(times[-1]-times[0]),]
                    
                    Ad.moments= pd.concat([Ad.moments,result])
                    print_status('Added',title)              
        else:
            pass
    else:
        pass
    return Ad


def add_moment_whole(Ad,raw):
    ###Check if data contains scene info
    if Ad.moments.loc[Ad.moments['Moment']=='Whole']['End'].values[0]==0:
        start_time = raw.loc[raw['SlideEvent']=='StartMedia']['Timestamp'].values[0]
        end_time = raw.loc[raw['SlideEvent']=='EndMedia']['Timestamp'].values[0]
        dur = end_time-start_time
        Ad.moments.loc[Ad.moments['Moment']=='Whole', 'End']=dur/1000
        Ad.moments.loc[Ad.moments['Moment']=='Whole', 'Duration']=dur/1000
        print_status('Added','Whole') 
    return Ad


def add_moment_annotation(Ad,path):
    scene_data = pd.read_csv(path, header=0)
    scenes = scene_data.loc[scene_data['SourceStimuliName']==Ad.name]

    for index,row in scenes.iterrows():
        result = pd.DataFrame()

        #start_time = row['Start Time (ms)']/1000
        #end_time = row['End Time (ms)']/1000
        start_time = row['SceneStart']/1000
        end_time = row['SceneEnd']/1000
        result['Moment']=[row['Scene']]
        result['Start']=[start_time]
        result['End']=[end_time]
        result['Duration']=[end_time-start_time,]
                    
        Ad.moments= pd.concat([Ad.moments,result])
        print_status('Added',row['Scene'])
    return Ad
 

def update_ads(in_folder, out_folder, results_folder, ad = None, ):
    ### Get raw files
    files = get_files(in_folder, tags=['.csv',])
    
    for file in files:
        respondent = file.split('.')[0]
        header(f'Now Working {respondent}')

        raw = read_imotions(f'{in_folder}{file}')

        if all(x in raw.columns for x in ['High Engagement','Workload Average','Frontal Asymmetry Alpha']):
            #Fetch Stimuli List
            stimuli = raw['SourceStimuliName'].drop_duplicates().tolist()
            if ad is not None:
                stimuli = [i for i in stimuli if ad in i]
        
        
            for stimulus in stimuli:
                print_step('Updating',stimulus)    
                path = f"{out_folder}"
                os.makedirs(path, exist_ok=True)

                ### Open Pickle
                Ad = get_pickle(path,stimulus)

                ### Do Work
                stimuli_raw_data = raw.loc[raw['SourceStimuliName']==stimulus]
                #stimuli_raw_data.to_csv(f'{stimulus}.csv')

                Ad = add_raw_data(Ad,respondent,stimuli_raw_data)
                Ad = add_moment_whole(Ad,stimuli_raw_data)
                Ad = add_moments(Ad,stimuli_raw_data)
            
                print_status('Saving',save_pickle(Ad, path))
                backup_files(out_folder)
        else:
            print_status('Excluded',respondent)


def update_scenes(in_folder, out_folder, results_folder, scene_path, ad = None):
    ### Get raw files
    if ad is None:
        ads = get_files(out_folder, tags=['.pickle'])
        ads = [i.split('.')[0] for i in ads]
    else:
        ads = get_files(out_folder, tags=['.pickle',ad])
        ads = [i.split('.')[0] for i in ads]

    for ad in ads:
        #header(f'Now Showing {ad}')
        
        try:
            Ad = get_pickle(out_folder,ad)
            
            Ad = add_moment_annotation(Ad,scene_path)

            print_status('Saving',save_pickle(Ad, out_folder))
            
        except Exception as z:
            print_status('Failed to Show',f"{ad} - {z!r}")


def update_metrics(in_folder, out_folder, results_folder, ad = None):
    ### Get raw files
    if ad is None:
        ads = get_files(out_folder, tags=['.pickle'])
        ads = [i.split('.')[0] for i in ads]
    else:
        ads = get_files(out_folder, tags=['.pickle',ad])
        ads = [i.split('.')[0] for i in ads]

    for ad in ads:
        #header(f'Now Showing {ad}')
        
        try:
            Ad = get_pickle(out_folder,ad)
            
            Ad = calc_averages(Ad)
            
            cols = ['Frontal Asymmetry Alpha',
                'High Engagement',
                'Optimal Workload',
                'Low Workload',
                'Overworked',
                'Low Engagement',
                'Distraction',
                'Drowsy',
                'Workload Average',]
            
            for index, row in Ad.moments.iterrows():
                for c in cols:
                    Ad=calc_moment_metric(Ad,c,row['Moment'], row['Start'], row['End'])
            
            print_status('Saving',save_pickle(Ad, out_folder))
            
        except Exception as z:
            print_status('Failed to Show',f"{ad} - {z!r}")


def update_time_series(in_folder, out_folder, results_folder, ad = None):
    ### Get raw files
    if ad is None:
        ads = get_files(out_folder, tags=['.pickle'])
        ads = [i.split('.')[0] for i in ads]
    else:
        ads = get_files(out_folder, tags=['.pickle',ad])
        ads = [i.split('.')[0] for i in ads]

    for ad in ads:
        #header(f'Now Showing {ad}')
        
        try:
            Ad = get_pickle(out_folder,ad)
            
            plot_time_series(Ad,results_folder)
            
            print_status('Saving',save_pickle(Ad, out_folder))
            
        except Exception as z:
            print_status('Failed to Show',f"{ad} - {z!r}")




def calc_averages(Ad):
    print_status('Calculating Averages',Ad.name)
    
    low_threshold = 0.4
    overworked_threshold = 0.6
    
    metrics = {'Frontal Asymmetry Alpha':128,
                      'High Engagement':256,
                      'Low Engagement':256,
                      'Distraction':256,
                      'Drowsy':256,
                      'Workload Average':256}
    
    for key,value in metrics.items():
        print_status('>> Calculating',key)
        
        if key == 'Workload Average':
            raw = Ad.signals['Workload Average']           
            results = pd.DataFrame()            
            times = raw['Time'].drop_duplicates()
            
            for t in times:
                data = raw.loc[raw['Time']==t]['Value']
                
                low = sum(1 for item in data if item < low_threshold)
                optimal = sum(1 for item in data if item > low_threshold and item < overworked_threshold)
                overworked = sum(1 for item in data if item > overworked_threshold)
                count = len(data)
                if count>0:
                    low = low/count*100
                    optimal = optimal/count*100
                    overworked = overworked/count*100
                else: 
                    count = 0
                    low = 0
                    optimal = 0
                    overworked = 0
                workload = data.mean()
                
                result = pd.DataFrame()
                result['Time']=[t]
                result['Low Workload']=[low]
                result['Optimal Workload']=[optimal]
                result['Overworked']=[overworked]
                result['Workload Average']=[workload]
                
                results = pd.concat([results,result])
            
            wl_metrics = ['Low Workload','Optimal Workload','Overworked','Workload Average']
            
            for wl_metric in wl_metrics:
                Ad.averages[wl_metric] = pd.DataFrame()
                Ad.averages[wl_metric].loc[:,'Time']=results['Time']
                Ad.averages[wl_metric].loc[:,'Value']=results[wl_metric]
                #Ad.averages[wl_metric].loc[:,'Filtered']=results[wl_metric]
                Ad.averages[wl_metric].loc[:,'Filtered']=(100/(1+np.exp(-(12*(results[wl_metric].values/100)-5))))
   
        else:
            try:
                Ad.averages[key] = pd.DataFrame()
                data = Ad.signals[key][['Time','Value']].groupby('Time').mean()
                data.loc[:,'Time']=data.index
                #print(data)
                Ad.averages[key]=data.copy()
                #print(Ad.averages[key])
                ### S-Curve
                if key == 'Frontal Asymmetry Alpha':     
                    Ad.averages[key].loc[:,'Filtered']=np.sign(data['Value'].values)*0.5/(1+np.exp(-(12*np.abs(data['Value'].values)-5)))
                elif key == 'High Engagement':
                    #Ad.signals[key].loc[:, 'SCurve']=(100/(1+np.exp(-(19.8*Ad.signals[key]['Value'].values-5))))
                    # data = Ad.signals[key].groupby('Time').mean()
                    # data.loc[:,'Time']=data.index
                    Ad.averages[key].loc[:,'Filtered']=(100/(1+np.exp(-(15*data['Value'].values-5))))
                
                else:
                    Ad.averages[key].loc[:,'Filtered']=(100/(1+np.exp(-(12*data['Value'].values-5))))
                    #Ad.averages[key].loc[:,'Filtered']=data['Value']*100
                    pass
            except:
                print(f'>>>> Failed on {key}')
                pass
            
    print_status('Completed Averages',Ad.name)
    
    return Ad


def calc_moment_metric(Ad, metric, moment= None, t0=None,tf=None):
    print_status('Calculating Moments',moment)
    try:
        result = Ad.averages[metric].loc[
            (Ad.averages[metric]['Time']>=t0)&
            (Ad.averages[metric]['Time']<=tf)]['Filtered'].mean()
        Ad.moments.loc[Ad.moments['Moment']==moment, metric] = result      
        print_status(f'Updated {metric} on {moment}',result)
    except Exception as z:
        print_status(f'Failed to Update {metric} on {moment}',f"{Ad.name} - {z!r}")
    print_status('>> Calculating Moments',moment)
    return Ad


def calculate_percentiles(df, ind, cols):
    # Initialize an empty DataFrame to hold calculations
    calc = pd.DataFrame()
    
    # Calculate means and standard deviations for the specified columns
    col_means = {x: df[x].mean() for x in cols}
    col_stds = {x: df[x].std() for x in cols}

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        # Calculate percentiles for each column
        _per = {f"Percentile_{x}": 100 * norm.cdf((row[x] - col_means[x]) / col_stds[x]) for x in cols}
        
        # Create a dictionary for the current row, including the index column
        _calc = {ind: row[ind]}
        _calc.update(_per)
        
        # Fix: Explicitly pass an index when creating the new DataFrame
        row_df = pd.DataFrame(_calc, index=[index])
        
        # Concatenate the newly created DataFrame with the existing calculations
        calc = pd.concat([calc, row_df])

    return calc

            
def compile_results(in_folder, out_folder, results_folder):
    ads = get_files(out_folder, tags=['.pickle'])
    ads = [i.split('.')[0] for i in ads]
   
    results = pd.DataFrame()
        
    for ad in ads:
        #header(f'Now Working {ad}')
        
        try:
            Ad = get_pickle(out_folder,ad)
            results = pd.concat([results,get_core_metrics(Ad)])
        except Exception as z:
            print_status('Failed to Update',f"{ad} - {z!r}")
    
    percentiles = calculate_percentiles(results, 'Name', ['Core']).rename(columns={'Percentile_Core':'AdNeuro'}).set_index('Name')
    results = results.set_index('Name')
    results = pd.concat([results,percentiles], axis=1)
    
    #results['Name']=results.index
    #print(results)
    
    results = results.sort_values(by='AdNeuro', ascending=False)
    results = results.reset_index()
    results.to_csv(f'{results_folder}AdNeuro_Results.csv')
    print(results[['Name','AdNeuro']])

def compile_results_scenes(in_folder, out_folder, results_folder):
    ads = get_files(out_folder, tags=['.pickle'])
    ads = [i.split('.')[0] for i in ads]
   
    results = pd.DataFrame()
        
    for ad in ads:
        #header(f'Now Working {ad}')
        
        try:
            Ad = get_pickle(out_folder,ad)
            results = pd.concat([results,get_scene_metrics(Ad)])
        except Exception as z:
            print_status('Failed to Update',f"{ad} - {z!r}")
    
    percentiles = calculate_percentiles(results, 'ID', ['Core']).rename(columns={'Percentile_Core':'AdNeuro'}).set_index('ID')
    results = results.set_index('ID')
    results = pd.concat([results,percentiles], axis=1)
    
    #results['Name']=results.index
    #print(results)
    
    results = results.sort_values(by='AdNeuro', ascending=False)
    results = results.reset_index()
    results.loc[:, 'Motivation']=(results['Frontal Asymmetry Alpha']+0.5)*100
    results = results.rename(columns={'High Engagement':'Engagement','Optimal Workload':'Efficiency'})
    results = results[['ID', 'Moment', 'Motivation', 'Engagement', 'Efficiency', 'Core', 'AdNeuro', 'Start', 'End', 'Duration', 'Frontal Asymmetry Alpha', 'Low Workload', 'Overworked', 'Low Engagement', 'Distraction', 'Drowsy', 'Workload Average', 'Name']]
    results.to_csv(f'{results_folder}AdNeuro_Results_Scenes.csv')
    print(results[['Name','AdNeuro']])
    
def show_scores(in_folder, out_folder, results_folder):
    ads = get_files(out_folder, tags=['.pickle'])
    ads = [i.split('.')[0] for i in ads]

    for ad in ads:
        header(f'Now Showing {ad}')
        
        try:
            Ad = get_pickle(out_folder,ad)
            #print(Ad.moments)
            
            #data = Ad.signals['Frontal Asymmetry Alpha'].groupby('Time').mean()
            #print(data['Value'].mean())
            #print(Ad.averages['Frontal Asymmetry Alpha

            

            #alpha = Ad.averages['Frontal Asymmetry Alpha'].reset_index(drop=True).sort_values(by='Time')
            #eng = Ad.averages['High Engagement'].reset_index(drop=True).sort_values(by='Time')
            #wl = Ad.averages['Workload Average'].reset_index(drop=True).sort_values(by='Time')


            #xs = {'Alpha':alpha['Time'].to_numpy(),
            #        'Eng':eng['Time'].to_numpy(),
            #        'WL':wl['Time'].to_numpy()}
            #ys = {'Alpha':(alpha['Value'].to_numpy()+0.5)*100,
            #        'Eng':eng['Value'].to_numpy()*100,
            #        'WL':wl['Value'].to_numpy()*100}

            #results['Time']=xs['Eng']
            #results['Raw']=eng['Value'].to_numpy()
            #results['Filt']=ys['Eng']

            for m in ['High Engagement']:
                Ad.signals[m].to_csv(f'{results_folder}{Ad.name}_Signals_{m}.csv')
                Ad.averages[m].to_csv(f'{results_folder}{Ad.name}_Averages_{m}.csv')
            
        except Exception as z:
            print_status('Failed to Show',f"{ad} - {z!r}")
 
            
def get_core_metrics(Ad):
    result = pd.DataFrame()
    result['Name']=[Ad.name]
    df = Ad.moments
    #print_status('Getting Core Metrics',Ad.name)
    ### Standard
    motivation = (df.loc[df['Moment'].str.contains('Brand')]['Frontal Asymmetry Alpha'].values[0]+0.5)*100
    #motivation = (df.loc[df['Moment']=='Whole']['Frontal Asymmetry Alpha'].values[0]+0.5)*100
    engagement = df.loc[df['Moment']=='Whole']['High Engagement'].values[0]
    efficiency = df.loc[df['Moment']=='Whole']['Optimal Workload'].values[0]

    loweng = df.loc[df['Moment']=='Whole']['Low Engagement'].values[0]
    drowsy = df.loc[df['Moment']=='Whole']['Drowsy'].values[0]
    distraction = df.loc[df['Moment']=='Whole']['Distraction'].values[0]
    wlavg = df.loc[df['Moment']=='Whole']['Workload Average'].values[0]*100
    #wlavg = butter_lowpass_filter(wlavg, 0.06, 0.5, order=2)
    
    ### Brand Connection
    #motivation = (df.loc[df['Moment'].str.contains('rand')]['Frontal Asymmetry Alpha'].values[0]+0.5)*100
    #engagement = df.loc[df['Moment'].str.contains('rand')]['High Engagement'].values[0]
    #efficiency = df.loc[df['Moment'].str.contains('rand')]['Optimal Workload'].values[0]
    
    ### Any Alpha Whole
    #motivation = np.abs(df.loc[df['Moment']=='Whole']['Frontal Asymmetry Alpha'].values[0])/0.5*100
#     engagement = df.loc[df['Moment']=='Whole']['High Engagement'].values[0]
#     efficiency = df.loc[df['Moment']=='Whole']['Optimal Workload'].values[0]

#     ### Any Alpha distraction
#     motivation = np.abs(df.loc[df['Moment']=='Whole']['Frontal Asymmetry Alpha'].values[0])/0.5*100
#     engagement = df.loc[df['Moment']=='Whole']['High Engagement'].values[0]-df.loc[df['Moment']=='Whole']['Distraction'].values[0]-df.loc[df['Moment']=='Whole']['Drowsy'].values[0]
#     efficiency = df.loc[df['Moment']=='Whole']['Optimal Workload'].values[0]
    
    core = (motivation+engagement+efficiency)/3
    
    result['Motivation']=[motivation]
    result['Engagement']=[engagement]
    result['Efficiency']=[efficiency]
    result['Low Engagement']=[loweng]
    result['Drowsy']=[drowsy]
    result['Distraction']=[distraction]
    result['Workload']=[wlavg]
    result['Core']=[core]
    
    return result

def get_scene_metrics(Ad):
    result = Ad.moments
    result['Name']=Ad.name
    result['Group']=Ad.name.split("_")[-1]
    result['ID']=result['Name'].astype(str)+ "_"+result['Moment'].astype(str)
    result['Core']=(result['Frontal Asymmetry Alpha'].values+0.5*100+result['High Engagement']+result['Optimal Workload'])/3

    return result

### For Nez
def rename_stims(in_folder):
    files = get_files(f'{in_folder}',tags=['.csv',])
    for file in files:
        try:
            df = read_imotions(f'{in_folder}{file}')
            #r = int(file.split('.csv')[0].split('_')[-1])
            #group = 'Treatment' if int(r.split('_')[1].split('.')[0][:2])>15 else 'Control'
            #key = pd.read_csv(f'{results_folder}key.csv')
            #gender = key.loc[key['Respondent']==r]['Gender'].values[0]
            #df['SourceStimuliName']=df['SourceStimuliName'].astype(str)+ f'_{gender}'
            for stim in  df['SourceStimuliName'].drop_duplicates().tolist():
                start=df.loc[(df['SourceStimuliName']==stim)
                                &(df['SlideEvent']=='StartMedia')]['Timestamp'].values[0]
                df.loc[(df['SourceStimuliName']==stim), 'Timestamp']=df.loc[(df['SourceStimuliName']==stim)]['Timestamp']-start

            df['SourceStimuliName']= df['SourceStimuliName'].apply(lambda x: '_'.join(x.split('_')[:-1]))
            df.to_csv(f'{in_folder}{file}')
            print_status('Renamed',r)
        except:
            print_status('Failed Rename',r)
            pass


def parse_two_viewings(in_folder):
    files = get_files(f'{in_folder}',tags=['.csv',])
    for file in files:
        try:
            df = read_imotions(f'{in_folder}{file}')

            for stim in  df['SourceStimuliName'].drop_duplicates().tolist():
                start=df.loc[(df['SourceStimuliName']==stim)
                                &(df['SlideEvent']=='StartMedia')]['Timestamp'].values[0]
                df.loc[(df['SourceStimuliName']==stim), 'Timestamp']=df.loc[(df['SourceStimuliName']==stim)]['Timestamp']-start

            df['SourceStimuliName'] = df['SourceStimuliName'].replace({'Royovac_Imagine Your Life_15_01-1':'Royovac_Imagine Your Life_15_02',
                                              })
            df['SourceStimuliName']= df['SourceStimuliName'].apply(lambda x: '_'.join(x.split('_')[:-1]))

            ### Change column to "AOIs gazed at"
            try:
                df = df.rename({"Respondent Annotations active":"AOIs gazed at"},axis=1)
                df["AOIs gazed at"]=df['AOIs gazed at'].replace(" dwelled on","")
            except:
               print(f">>>>> ET: No ET for {file}")
               pass

            df.to_csv(f"{in_folder}{file}")
            print_status('Parsed',file)
        except:
            print_status('Failed Rename',file)
            pass


def create_splits(in_folder):
    files = get_files(f'{in_folder}',tags=['.csv',])
    for file in files:
        try:
            df = read_imotions(f'{in_folder}{file}')
            #resp = int(file.split('_')[2].split('.')[0])
            df = df.loc[df['SourceStimuliName'].str.contains('LBTD')]

            # for stim in  df['SourceStimuliName'].drop_duplicates().tolist():
            #     if resp in [20, 24, 25, 29, 30, 12, 14, 21, 22, 5, 7, 4, 26, 6]:
            #         df.loc[(df['SourceStimuliName']==stim), 'SourceStimuliName']=df['SourceStimuliName'].astype(str) + '_TA'
            #     else: 
            #         df.loc[(df['SourceStimuliName']==stim), 'SourceStimuliName']=df['SourceStimuliName'].astype(str) + '_NT'

            df.to_csv(f'C:/Users/ashra/Documents/NeuralSense/infiles/VW_Only/{file}')
            print_status('Parsed',file)
        except:
            print_status('Failed Rename',file)
            pass


def plot_time_series(Ad,results_folder):
    out_path = f"{results_folder}AdNeuro_Graphs/"
    os.makedirs(out_path, exist_ok=True) 

    print(f">> Now Plotting: {Ad.name}")
    y_dim = 3.6417323
    x_dim = 13.3346457
    labels = ['Alpha','Eng','WL']

    colors = {'Alpha':'black',
            'Eng':'steelblue',
            'WL':'deepskyblue'}

    alpha = Ad.averages['Frontal Asymmetry Alpha'].reset_index(drop=True).sort_values(by='Time')
    eng = Ad.averages['High Engagement'].reset_index(drop=True).sort_values(by='Time')
    wl = Ad.averages['Workload Average'].reset_index(drop=True).sort_values(by='Time')
    #ow = Ad.averages['Overworked'].reset_index(drop=True).sort_values(by='Time')


    xs = {'Alpha':alpha['Time'].to_numpy(),
            'Eng':eng['Time'].to_numpy(),
            'WL':wl['Time'].to_numpy()}
    ys = {'Alpha':(alpha['Filtered'].to_numpy()+0.5)*100,
            'Eng':eng['Filtered'].to_numpy(),
            'WL':wl['Value'].to_numpy()*100}



    plt.rcParams['axes.edgecolor']='#333F4B'
    plt.rcParams['axes.linewidth']=0.8
    plt.rcParams['xtick.color']='#333F4B'
    plt.rcParams['ytick.color']='#333F4B'
    plt.rcParams['text.color']='#333F4B'

    fig = plt.figure()

    ax = fig.add_subplot(111)

    # change the style of the axis spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.spines['left'].set_position(('outward', 8))
    ax.spines['bottom'].set_position(('outward', 5))

    axes = plt.gca()
    axes.get_xaxis().set_visible(False)

    #plt.title(title, fontsize=12)
    plt.xlim(0,xs['Alpha'].max())
    plt.ylim(0,100)
    plt.yticks(ha='left',rotation=90,fontsize=7,  )

    for label in labels:
        plt.plot(xs[label],ys[label],label = label, color = colors[label],linewidth=3)
    #if legend:
    #    plt.legend()

    fig.set_size_inches(x_dim, y_dim)
    plt.savefig(f'{out_path}plot_{Ad.name}_Composite.png', dpi=300, transparent=True)
    plt.close()

    for label in labels:
        fig = plt.figure()

        ax = fig.add_subplot(111)

        # change the style of the axis spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        ax.spines['left'].set_position(('outward', 8))
        ax.spines['bottom'].set_position(('outward', 5))

        axes = plt.gca()
        axes.get_xaxis().set_visible(False)

        #plt.title(title, fontsize=12)
        plt.xlim(0,xs['Alpha'].max())
        plt.ylim(0,100)
        plt.yticks(ha='left',rotation=90,fontsize=7,  )
        plt.plot(xs[label],ys[label],label = label, color = colors[label],linewidth=3)
        fig.set_size_inches(x_dim, y_dim)
        plt.savefig(f'{out_path}plot_{Ad.name}_{label}.png', dpi=300, transparent=True)
        plt.close()
    

def get_split_results(in_folder, out_folder, results_folder):
    out_path = f"{results_folder}"
    files = get_files(f'{out_folder}')
    ads = ['_'.join(f.split('_')[:-1]) for f in files]
    ads = clean.drop_duplicates(ads)

    for ad in ads:
        paths = [p for p in files if ad in p]
        genders = [p.split('.')[0].split('_')[-1] for p in paths]

        genders_data = {}
        for g in genders:
            path = [p for p in paths if g in p][0]
            ad_name = path.split('.')[0]
            Ad = get_pickle(out_folder,ad_name)
            genders_data[g]=Ad

        metrics = ['Frontal Asymmetry Alpha', 'High Engagement', 'Workload Average']
        for metric in metrics:
            seconds = genders_data['Male'].averages[metric]['Time'].values                 
            significance = pd.DataFrame()   
            for second in seconds:
                stats_seconds = {}
                for gender in genders:
                    data = genders_data[gender].signals[metric]
                    second_data = data.loc[data['Time']==second]['Value'].values
                    stats_seconds[gender] = second_data
                    
                significance = pd.concat([significance, get_significance(stats_seconds, genders, f'{second}')])
        
            significance = significance.drop_duplicates(subset=['Cluster'])
            significance.to_excel(f'{results_folder}{ad}_{metric}_PerSecond_Significance.xlsx', index = False)

        print(f">> Now Plotting: {Ad.name}")
        y_dim = 3.6417323
        x_dim = 13.3346457
        colors = {'Male':'steelblue',
                'Female':'deepskyblue'}
        plt.rcParams['axes.edgecolor']='#333F4B'
        plt.rcParams['axes.linewidth']=0.8
        plt.rcParams['xtick.color']='#333F4B'
        plt.rcParams['ytick.color']='#333F4B'
        plt.rcParams['text.color']='#333F4B'

        for metric in metrics:
            fig = plt.figure()
            ax = fig.add_subplot(111)

            # change the style of the axis spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            ax.spines['left'].set_position(('outward', 8))
            ax.spines['bottom'].set_position(('outward', 5))

            axes = plt.gca()
            axes.get_xaxis().set_visible(False)

            #Get x
            x = genders_data['Male'].averages[metric]['Time'].values     


            #plt.title(title, fontsize=12)
            plt.xlim(0,x.max())
            plt.ylim(0,100)
            plt.yticks(ha='left',rotation=90,fontsize=7,  )

            for gender in genders:
                x = genders_data[gender].averages[metric]['Time'].values
                if metric=='Frontal Asymmetry Alpha':
                    y = (genders_data[gender].averages[metric]['Filtered'].values+0.5)*100
                elif metric=='Workload Average':
                    y = (genders_data[gender].averages[metric]['Filtered'].values)*100
                else:
                    y = (genders_data[gender].averages[metric]['Filtered'].values)
                plt.plot(x,y,label = gender, color = colors[gender],linewidth=3)

            fig.set_size_inches(x_dim, y_dim)
            plt.savefig(f'{out_path}plot_Split_{ad}_{metric}.png', dpi=300, transparent=True)
            plt.close()



    # Get statistical significance for each second
    # Plot graphs on top of each other
     
def eye_metrics_saliency(in_folder, results_folder):
       
    print("> Running: Extracting Eye Metrics")
    in_path = f"{in_folder}"
    out_path = f"{results_folder}AdNeuro_EyeTracking/"
    os.makedirs(out_path, exist_ok=True)          
    files = get_files(in_path)
    #Create the things we will need
    col  = ['Res','Slide','AOI','Timestamp','Index','Duration']
    calc = []

    # #Extracting all raw data

    # ### FOR EACH PARTICIPANT
    # for f in files:
    #     try:
    #         df = read_imotions(f"{in_path}{f}")
    #         df= df.reset_index()
    #         stims = df['SourceStimuliName'].drop_duplicates()

    #         res = '_'.join(f.split('.csv')[0].split('_')[1:])
    #         #group = 'Treatment' if int(res.split('_')[1].split('.')[0][:-1])>15 else 'Control'  

    #         #stims = [f'{x}_{group}' for x in stims]

    #         for stim in stims: #For each ad, skip this as data should already be split by ad
    #             adn = stim#'_'.join(stim.split('_')[:-1])
    #             _stim = df[df['SourceStimuliName']== adn]

    #             #Get list of AOIs viewed by participant - ALREADY DONE
    #             aois = _stim['AOIs gazed at'].dropna().drop_duplicates()

    #             #Get start time - ALREADY DONE
    #             _start_time = _stim.loc[_stim['SlideEvent']=='StartMedia']['Timestamp'].iloc[0]

    #             #Get data per AOI
    #             for aoi in aois:
                    
    #                 #Collect all data for the AOI, adjust the timestamp to start of ad
                    
    #                 _aoi = _stim.loc[_stim['AOIs gazed at']==aoi]
    #                 col = ['Row','Timestamp','FixIndex','FixDur','Stim','Respondent']
    #                 _pupil = pd.DataFrame(columns= col)
    #                 _pupil['Row'] = _aoi['Row']
    #                 _pupil['Timestamp']=_aoi['Timestamp']-_start_time
    #                 _pupil['FixIndex']=_aoi['Fixation Index']
    #                 _pupil['FixDur']=_aoi['Fixation Duration']
    #                 _pupil['Stim']=stim
    #                 _pupil['Respondent']= f[:11]

    #                 #Find all fixations for the ad
    #                 ### FIXATIONS IDENTIFIED BY INDEX
    #                 fixations = _pupil['FixIndex'].drop_duplicates().dropna()
                    
    #                 ### THIS IS COLLECTING ALL FIXATIONS FOR AN AOI, ROW ENTRY PER FIXATION
                    
    #                 #For each fixation
    #                 for fix in fixations:
    #                     _data = _pupil.loc[_pupil['FixIndex']==fix]

    #                     _calc = {'Res':_data['Respondent'].iloc[0],
    #                             'Stim':stim,
    #                             'AOI':aoi,
    #                             'Timestamp':_data['Timestamp'].iloc[0], #Identify start time of fixation from time of first appearance of fixation index
    #                             'Index':_data['FixIndex'].iloc[0],
    #                             'Duration':_data['Timestamp'].iloc[-1]-_data['Timestamp'].iloc[0]} #Set duration of fixation by time of last entry minus time of first entry
    #                     calc.append(_calc)

    #                 #BY THE END OF THIS, WE HAVE A TABLE WITH A ROW ENTRY FOR EACH FIXATION OF EACH PARTICIPANT
    #         print(f">> Completed Collection: {f} ")
    #     except Exception as z:
    #             get_key(z)  
    
    # #File containing eye data per ad per fixations
    # calc = pd.DataFrame(calc)
    # calc.to_excel(f'{out_path}eye_metrics_raw.xlsx', index = False)

    # og = len(calc)
    # calc = calc.loc[(calc['Duration']>=150)]
    # calc = calc.loc[(calc['Duration']<=900)]
    # new = len(calc)
    # print(f'>>>>>> Discarded {og-new} fixations')

    # calcs = []

    # resps = calc['Res'].drop_duplicates()
    
    # #Calculating metrics from raw (FFD and TFD)
    # for res in resps:                
    #     _res = calc.loc[calc['Res']==res]
    #     stims = _res['Stim'].drop_duplicates()

    #     for stim in stims:
    #         _stim = _res[_res['Stim']== stim].sort_values('Timestamp')
    #         aois = _stim['AOI'].dropna().drop_duplicates()

    #         for aoi in aois:
    #             _aoi = _stim.loc[_stim['AOI']==aoi].sort_values('Timestamp')
    #             _calcs = {'Res':res,
    #                     'Stim':stim,
    #                     'AOI':f"{stim}_{aoi}",
    #                     'Timestamp':_aoi['Timestamp'].iloc[0],
    #                     'Index':_aoi['Index'].iloc[0],
    #                     'TFD':_aoi['Duration'].sum(),
    #                     'FFD':_aoi['Duration'].iloc[0]}

    #             calcs.append(_calcs)

    # calcs = pd.DataFrame(calcs)
    # calcs.to_excel(f'{out_path}eye_metrics_final.xlsx', index = False)
    
    calcs = pd.read_excel(f'{out_path}eye_metrics_final.xlsx')
    data = calcs

    # Separate numeric columns and non-numeric columns
    numeric_columns = data.select_dtypes(include='number').columns
    non_numeric_columns = data.select_dtypes(exclude='number').columns

    # Perform groupby operation on numeric columns only for AOI
    data_numeric = data.groupby(['AOI'])[numeric_columns].mean()

    # Handle non-numeric columns for AOI
    for col in non_numeric_columns:
        data_numeric[col] = data.groupby('AOI')[col].first()


    # Ensure 'AOI' column is included correctly
    data_numeric['AOI'] = data_numeric.index

    # Save the result to an Excel file for AOI
    data_numeric.to_excel(f'{out_path}RESULT_AOI_Performance.xlsx', index=False)

    # Read the saved AOI performance data
    data = pd.read_excel(f'{out_path}RESULT_AOI_Performance.xlsx')

    # Apply percentiles_df function to AOI data
    data2 = percentiles_df(data, 'AOI', ['TFD', 'FFD'])

    # Save the result to an Excel file for AOI percentiles
    data2.to_excel(f'{out_path}RESULT_AOI_percentiles.xlsx', index=True)

    # Perform groupby operation on numeric columns only for Stim
    data2_numeric = data.groupby(['Stim'])[numeric_columns].sum()

    data2_numeric.reset_index(inplace=True)

    # Apply percentiles_df function to Stim data
    data2_numeric = percentiles_df(data2_numeric, 'Stim', ['TFD'])

    # Save the result to an Excel file for Brand Prominence
    data2_numeric.to_excel(f'{out_path}RESULT_Brand_Prominence.xlsx', index=True)

    print("> Completed: Percentiles")
    return calc

def percentiles_df(in_df, ind, cols):
    header(f"> Running: Calculating Percentiles")
    
    #Define variables
    calc = [] 
    
    col_means = {x:in_df[x].mean() for x in cols}
    col_stds = {x:in_df[x].std() for x in cols}

    for index, row in in_df.iterrows():
        _per = {f"Percentile_{x}":100*norm.cdf((row[x]-col_means[x])/col_stds[x]) for x in cols}
        _calc = {f'{ind}':row[ind],}
        _calc.update(_per)       
        calc.append(_calc)


    print("> Completed: Percentiles")
    return pd.DataFrame(calc)


def rename_files_in_directory(directory_path, extension):
    try:
        # List all files in the directory
        files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        
        for file_name in files:
            # Split the file name and its extension
            file_root, file_extension = os.path.splitext(file_name)
            
            # Construct the new file name
            new_file_name = file_root + extension + file_extension
            
            # Rename the file
            os.rename(
                os.path.join(directory_path, file_name),
                os.path.join(directory_path, new_file_name)
            )
        print("All files renamed successfully!")
    
    except Exception as e:
        print(f"An error occurred: {e}")


def GSR(in_folder,results_folder):
    
    task = "GSR"
    print("> Running: GSR")
    
    out_path = f"{results_folder}AdNeuro_Graphs/"
    os.makedirs(out_path, exist_ok=True)  
    
    #### EEG
    in_path = f"{in_folder}"

    #Get Ad names
    all_data = pd.DataFrame()

    keep = ['Row','SourceStimuliName','Tonic Signal','Peak Detected','Timestamp','SlideEvent']
    metrics = ['Tonic Signal','Peak Detected']
    files = get_files(f'{in_folder}',tags=['.csv','Resp'])
    data = pd.DataFrame()

    tonic_data = pd.DataFrame()
    phasic_data = pd.DataFrame()

    for file in files:
        try:
            clean = read_imotions(f'{in_folder}{file}')

            stims = clean['SourceStimuliName'].drop_duplicates().to_list()

            for s in stims:
                print(s)
                data = clean.loc[clean['SourceStimuliName']==s]
                start_time = data.loc[data['SlideEvent']=='StartMedia']['Timestamp'].values[0]
                data.loc[:, 'Time']=data['Timestamp']-start_time
                data = data.loc[data['Time']>=0]

                tonic_data = pd.concat([tonic_data,data[['Time','Tonic Signal','SourceStimuliName']]])
                phasic_data = pd.concat([phasic_data,data[['Time','Peak Detected','SourceStimuliName']]])

          
        except:
            print_status('Failed EEG',file)
            pass

    phasic_data.to_csv('./Self/results/phasic_data2.csv')
    #phasic_data = pd.read_csv('./Self/results/phasic_data.csv')
    stims = phasic_data['SourceStimuliName'].drop_duplicates().tolist()

    results = []
    for stim in stims:
        #tonic = tonic_data.loc[tonic_data['SourceStimuliName']== stim].groupby('Time').mean().reset_index()
        #tonic.index = pd.to_timedelta(tonic['Time'], unit='ms')
        #tonic = tonic['Tonic Signal'].resample('500L').mean().reset_index().dropna()

        phasic = phasic_data.loc[phasic_data['SourceStimuliName']== stim][['Time','Peak Detected']].groupby('Time').mean().reset_index()
        phasic.index = pd.to_timedelta(phasic['Time'], unit='ms')
        phasic = phasic['Peak Detected'].resample('500L').mean().reset_index()
        #phasic = phasic_data.loc[phasic_data['SourceStimuliName']== stim].groupby('Time').mean()


        print(f">> Now Plotting: {stim}")
        y_dim = 3.6417323
        x_dim = 13.3346457
        colors = {'Male':'steelblue',
                'Female':'deepskyblue'}
        plt.rcParams['axes.edgecolor']='#333F4B'
        plt.rcParams['axes.linewidth']=0.8
        plt.rcParams['xtick.color']='#333F4B'
        plt.rcParams['ytick.color']='#333F4B'
        plt.rcParams['text.color']='#333F4B'

        
        fig = plt.figure()
        ax = fig.add_subplot(111)

        # change the style of the axis spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        ax.spines['left'].set_position(('outward', 8))
        ax.spines['bottom'].set_position(('outward', 5))

        axes = plt.gca()
        axes.get_xaxis().set_visible(False)

        #Get x
        x = phasic['Time'].values/1000     


        #plt.title(title, fontsize=12)
        plt.xlim(0,x.max())
        #plt.ylim(0,10)
        plt.yticks(ha='left',rotation=90,fontsize=7,  )

        y = phasic['Peak Detected'].values
           
        plt.plot(x,y,label = 'Phasic', color = colors['Male'],linewidth=3)

        fig.set_size_inches(x_dim, y_dim)

        result = pd.DataFrame()
        result['Time']=x
        result['Phasic']=y
        result.to_csv(f'{out_path}{stim}_Phasic.csv')

        plt.savefig(f'{out_path}plot_{stim}_Phasic.png', dpi=300, transparent=True)
        plt.close()

        result = {}
        result['Stim']=stim
        result['GSR']=y.sum()#area_under_curve(y, dx = x[1]-x[0])

        results.append(result)

    results = pd.DataFrame(results)
    results.to_csv(f'{results_folder}AdNeuro_GSR.csv')


def area_under_curve(y_values, dx=1):
    """
    Calculate the approximate area under a curve using the trapezoidal rule.
    
    :param y_values: A list of y-values sampled from the curve.
    :param dx: The spacing between consecutive x-values. Default is 1.
    :return: The approximate area under the curve.
    """
    # Ensure y_values is a list or a similar iterable with numeric values
    if not all(isinstance(y, (int, float)) for y in y_values):
        raise ValueError("All elements in y_values must be integers or floats.")
    
    # Calculate the area using the trapezoidal rule
    area = 0.5 * dx * sum(y_values[i] + y_values[i + 1] for i in range(len(y_values) - 1))
    
    return float(area)


def standard_analysis(scene_path=None):
    #update_ads(in_folder, out_folder, results_folder )
    
    # # # if scene_path is not None:
    # update_scenes(in_folder, out_folder, results_folder, scene_path=scene_path)

    # update_metrics(in_folder, out_folder, results_folder)
    # update_time_series(in_folder, out_folder, results_folder)

    # compile_results_scenes(in_folder, out_folder, results_folder)
    # compile_results(in_folder, out_folder, results_folder)
    
    GSR(in_folder,results_folder)
    #eye_metrics_saliency(in_folder,results_folder)

def main():
    #parse_two_viewings(in_folder)
    #create_splits(in_folder)
    standard_analysis(scene_path=annotation_path)
    #cities = ['JHB','CT']
    #orders = ['A','B']

    #for city in cities:
    #    for order in orders:
    #        path = f"../infiles/Data/{city}/{order}"
    #        rename_files_in_directory(path, f'_{city}_{order}')

    #empty_trash()
    #parse_two_viewings(in_folder)
    #update_ads(in_folder, out_folder, results_folder )
    #update_scenes(in_folder, out_folder, results_folder, scene_path=annotation_path)
    #update_metrics(in_folder, out_folder, results_folder)
    #update_time_series(in_folder, out_folder, results_folder)
    #show_scores(in_folder, out_folder, results_folder)

    ################ CHANGE THE ALPHA CALC BACK TO BRAND CONNECTION
    #compile_results_scenes(in_folder, out_folder, results_folder)
    #compile_results(in_folder, out_folder, results_folder)
    
    
    #eye_metrics_saliency(in_folder,results_folder)
    #get_split_results(in_folder, out_folder, results_folder)


if __name__ == "__main__":
    main()
