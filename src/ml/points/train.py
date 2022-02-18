from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold
from sklearn.model_selection import cross_val_score

from tqdm import tqdm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('bmh')
import os
os.chdir(os.path.join(os.getcwd(), '..', '..'))

run_name = 'run1_boiler'
data = os.path.join(os.getcwd(), 'saves', run_name+'.csv')
data = pd.read_csv(data, parse_dates=True, index_col=0)
data['noise'] = pd.Series(np.random.normal(size=len(data)), index=data.index)
data.drop(columns=['time_tuple', 'year', 'minute'], inplace=True)

workdays = [1, 2, 3, 4, 5]
data['weekday'] = data.weekday.apply(lambda day: 0. if day in workdays else 1.)

# remove non-varying entries
for feature in data.columns:
    if feature == 'month':
        continue

    std = data[feature].to_numpy().std()
    if std == 0.:
        data.drop(columns=[feature], inplace=True)
    else:
        col = data[feature].to_numpy()
        data[feature] =  pd.Series((col - col.mean()) / col.std(), index=data.index) 

targets = [col for col in data.columns if col.startswith('output')]
features = [col for col in data.columns if not col.startswith('output')]

val_month = 11
n_splits = 10

for target in tqdm(targets):
    print(f'Training model for target {target}.')

    # take November as testing data
    X_val = data.loc[data.month == val_month][features]
    y_val = data.loc[data.month == val_month][target]
    X_traintest = data.loc[data.month != val_month][features]
    y_traintest = data.loc[data.month != val_month][target]

    cv = KFold(n_splits=n_splits, random_state=1, shuffle=True)
    model = GradientBoostingRegressor()

    scores = cross_val_score(model, X_traintest, y_traintest, scoring='r2', cv=cv)
    print('R2 score for {}-fold CV: {} ({})'.format(n_splits, np.mean(scores), np.std(scores)))

    X_val, y_val = X_traintest, y_traintest

    model.fit(X_traintest, y_traintest)
    pred = model.predict(X_val)
    print(f'R2 on validation set: {r2_score(y_val, pred)}')

    fig, ax = plt.subplots(1, 1, figsize=(16, 4))
    pd.DataFrame({'ground truth': y_val, 'prediction': pred}).plot(ax=ax)
    ax.legend()
    ax.set_xlim(pd.Timestamp('2020-01-01'), pd.Timestamp('2020-03-01'))
    plt.show()
    






