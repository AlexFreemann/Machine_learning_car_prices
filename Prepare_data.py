import pandas as pd

#Load data
df=pd.read_csv('general_data_frame.csv')

#Delete Duplicates
df.drop_duplicates()


#Splite region in city and province
df['city']=[region.split(' (')[0] for region in df['region']]
df['province']=[region.split(' (')[-1][:-1] for region in df['region']]

#Translate fuel from polish to english
print(df['fuel'].unique())
#Create dictinory
fuel_eng={'Diesel' :'Diesel' ,'Benzyna+CNG':'CNG','Benzyna':'Gasoline', 'Benzyna+LPG':'LPG' , 'Hybryda':'Hybrid','Elektryczny': 'Electric'}
df['fuel_eng']=[fuel_eng[i] for i in df['fuel']]
print(df['fuel_eng'].unique())

#Clean price and mike it integers
print(df['price'])
df['price']=[int(i[:-4].replace(' ','')) for i in df['price']] #Slice 'PLN' and remove spaces

#Fix mistakes in mileage
def f(x):
    if 'cm3' in x: #if car is new we see here vol_engine
        x=0
    elif 'km' in x:
        x=int(x[:-2].replace(' ','')) # Delete km and spices
    else:
        x=x
    return x

df['mileage_clear']=[f(i) for i in df['mileage']]

##Clean vol
df['vol_engine']=[i.replace('cm3','').replace(' ','') for i in df['vol_engine']]#Slice 'cm3' and remove spaces
print(df['vol_engine'])

print(df['province'].unique())
print(len(df['city'].unique()))

#Create new df for kaggle (fewer and cleaner data)
df_kaggle=pd.DataFrame()
df_kaggle[['mark','model','generation_name','year','mileage','vol_engine','fuel','city','province','price']]=df[['mark','model','gen_name','year','mileage_clear','vol_engine','fuel_eng','city','province','price']]
print(df_kaggle)

#Save DataFrame
#You can find it on Kaggle: https://www.kaggle.com/aleksandrglotov/car-prices-poland
df_kaggle.to_csv('Car_Prices_Poland_Kaggle.csv')
