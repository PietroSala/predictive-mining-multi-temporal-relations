from re import S
import sys
import pandas as pd
import math
import warnings
import itertools
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)

# Function to read data from a CSV file given the name
def getData(fileName):
    df = pd.read_csv(fileName)
    return df

# Function to check if the values in antecedents columns are equal to a given row
def equalColumn(a, row, antecedents):
    for col in antecedents:
        if a.iloc[0][col] == row[col]:
            continue
        return False
    return True
    
# Recursive function to calculate approximate functional dependencies
def recADC(w, del_i, count_i, thresholds_d, antecedents):
    if len(w) == 0:
        return pd.DataFrame()
    columns = list(w.columns)
    num_col = len(columns)
    a = w.iloc[:1].drop(columns=[columns[0], columns[num_col-1]])
    for bool_val in [1, 0]:
        del_tuples = pd.DataFrame()
        s = pd.DataFrame()
        for i, row in w.iterrows():
            if equalColumn(a, row, antecedents):
                if row[columns[num_col-1]] != bool_val:
                    del_tuples = pd.concat([del_tuples, pd.DataFrame([row])], ignore_index=False)
                else:
                    s = pd.concat([s, pd.DataFrame([row])], ignore_index=False)
        out = []
        thresholds1_d = thresholds_d.copy()
        if not del_tuples.empty:
            count_d = {}
            for z in del_tuples[columns[0]]:
                if z not in count_d:
                    count_d[z] = 0
                count_d[z] += 1
            for z in set(del_tuples[columns[0]]):
                thresholds1_d[z] = thresholds_d[z] - count_d[z]
                if thresholds1_d[z] < 0 and 0 <= thresholds_d[z]:
                    out.append(z)
        if count_i - len(out) >= 0:
            count1_i = count_i - len(out)
            for i, row in w.iterrows():
                if not equalColumn(a, row, antecedents) and row[columns[0]] in out:
                    del_tuples = pd.concat([del_tuples, pd.DataFrame([row])], ignore_index=False)
            if del_i - len(del_tuples) >= 0:
                del1_i = del_i - len(del_tuples)
                w1_del = pd.concat([del_tuples, s], ignore_index=False)
                w1 = pd.merge(w, w1_del, how='outer', indicator=True).query('_merge == "left_only"').drop('_merge', axis=1)
                s1 = recADC(w1, del1_i, count1_i, thresholds1_d, antecedents)
                if not isinstance(s1, int):
                    return pd.concat([s, s1])
    return -1

# Function to start the program with initial error thresholds
def start_program(data, eg3, eh3, ej3, antecedents):
    id = data.columns[0]
    del_i = math.floor(eg3 * len(data))
    count_i = math.floor(eh3 * len(set(data[id])))
    count_d = {}
    thresholds_d = {}
    for z in data[id]:
        if z not in count_d:
            count_d[z] = 0
        count_d[z] += 1
    for z in data[id]:
        thresholds_d[z] = math.floor(ej3 * count_d[z])
    return recADC(data, del_i, count_i, thresholds_d, antecedents)

# Function to find the minimum error thresholds
def find_minimum(data, antecedents):
    eg3 = 1; eh3 = 1; ej3 = 1
    res = None
    while not isinstance(res, int) and eg3 >= 0:
        res = start_program(data, eg3, eh3, ej3, antecedents)
        eg3 -= 0.1
    eg3 += 0.2
    print('Minimum thresholds -> ',"%.1f"%eg3,'\t',end=' ')
    res = None
    while not isinstance(res, int) and eh3 >= 0:
        res = start_program(data, eg3, eh3, ej3, antecedents)
        eh3 -= 0.1
    eh3 += 0.2
    res = None
    print("%.1f"%eh3,'\t', end=' ')
    while not isinstance(res, int) and ej3 >= 0:
        res = start_program(data, eg3, eh3, ej3, antecedents)
        ej3 -= 0.1
    ej3 += 0.2
    print("%.1f"%ej3)

# Main function to execute the program
def main():
    argl = sys.argv[1:]
    data = getData(argl[0])
    eg3 = eh3 = ej3 = 1
    if len(argl) > 2:
        eg3 = float(argl[1])
        eh3 = float(argl[2])
        ej3 = float(argl[3])
    antecedents = list(data.columns[1:len(data.columns)-1])
    apfd_min = False
    print(argl[0],'\tg3: ',eg3,'\th3: ',eh3,'\tj3: ',ej3)
    print('\t\t\trows: ',len(data),'\tids: ',data[data.columns[0]].nunique())
    print('---------------------------------------------------------------------')
    for i, j in itertools.combinations(range(len(antecedents) + 1), 2):
        print('Evaluate APFD: ',antecedents[i:j],' => ',data.columns[len(data.columns)-1])
        if len(argl) > 2:
            res = start_program(data, eg3, eh3, ej3, antecedents[i:j])
            if not isinstance(res, int):
                print('<Resulting Set>\trows: ',len(res),'\tids: ',res[res.columns[0]].nunique(),'\n',res.to_string(index=False),'\n</Set>')
                for col in list(res.columns):
                    if col not in antecedents[i:j] and col != res.columns[len(res.columns)-1]:
                        res = res.drop(col, axis=1)
                res = res.groupby(antecedents[i:j] + [res.columns[len(res.columns)-1]]).size().reset_index(name='count').sort_values(by=['count'], ascending=False)
                print('Grouped Results\n',res.to_string(index=False))
            else:
                print('APFD does not hold with the specified input thresholds')
            print('---------------------------------------------------------------------')
        else:
            res = find_minimum(data, antecedents[i:j])

main()
