
# coding: utf-8

# In[ ]:

import pandas as pd
import datetime
pd.options.mode.chained_assignment = None  # default='warn'


# In[ ]:

#Read in csv
df = pd.read_csv(r'C:\Users\HHORNER\Documents\My MTA\Peoplesoft\Current\Current Peoplesoft.csv')


# In[ ]:

df.shape


# In[ ]:

#Drop data if Account Number/Service Type is null
df = df.dropna(subset=['Account Number/Service Type'])
df.shape


# In[ ]:

#Select used columns into psRaw
psRaw = df[['Vendor Name','Account Number/Service Type','Invoice Number','Invoice Date','Service Period',' Usage ','Unit of Measure','Actual or Estimated',' Amount ']]
psRaw[' Amount '] = psRaw[' Amount '].str.replace(',','')
psRaw[' Amount '] = psRaw[' Amount '].str.replace(' ','')
psRaw[' Amount '] = psRaw[' Amount '].str.replace('(','-')
psRaw[' Amount '] = psRaw[' Amount '].str.replace(')','')

psRaw.tail()


# In[ ]:

#Filter out unneeded Energy Types into psET (peoplesoft Energy Types)
ps = psRaw[psRaw['Account Number/Service Type'].str.contains('WATER|SEWER|STEAM')]
psET = ps[~ps['Vendor Name'].str.contains('CON EDISON')]
psET.shape


# In[ ]:

#Create Account Number column
psET['AccountNumber'] = psET['Account Number/Service Type'].str.split(' ').str[-1]
psET[['Account Number/Service Type','AccountNumber']]


# In[ ]:

#Remove '-' from Usage
psET.loc[psET[' Usage '].str.contains('-  '),' Usage '] = 0


# In[ ]:

#Create Read Type
psET['Read Type'] = ''
#If 'Actual or Estimated' contains ACTUAL, then 1, else 2
psET.loc[psET['Actual or Estimated'].str.contains('ACTUAL'),'Read Type'] = 1
psET.loc[~psET['Actual or Estimated'].str.contains('ACTUAL'),'Read Type'] = 2


# In[ ]:

#Create Delivery Charges
psET['DeliveryCharges'] = 0
#Replace all Nulls in 'Actual or Estimated' with ACTUAL
psET['Actual or Estimated'].fillna(value='ACTUAL',inplace=True)
#Replace all Nulls in 'Amount' with 0
psET[' Amount '].fillna(value=0,inplace=True)
#Set DeliveryCharges = Amount when 'Actual or Estimated' = ACTUAL OR ESTIMATE OR STEAM 
psET.loc[psET['Actual or Estimated'].str.contains('ACTUAL|STEAM|ESTIMATE|ESTIMATED'),'DeliveryCharges'] = psET[' Amount ']


# In[ ]:

#Create LateCharges
psET['LateCharges'] = 0
#Set LateCharges = Amount when 'Actual or Estimated' contains LATE 
psET.loc[psET['Actual or Estimated'].str.contains('LATE'),'LateCharges'] = psET[' Amount ']


# In[ ]:

#Create OtherCharges
psET['OtherCharges'] = 0
#Set OtherCharges = Amount when DeliveryCharges and LateCharges = 0
psET['OtherCharges'] = psET[' Amount '].astype(float) - (psET['DeliveryCharges'].astype(float) + psET['LateCharges'].astype(float))


# In[ ]:

#Create OtherChargesDescription
psET['OtherChargesDescription'] = ''
psET.loc[psET['OtherCharges'] != 0, 'OtherChargesDescription'] = psET['Actual or Estimated']


# In[ ]:

pd.set_option('display.max_rows', 1000)
psET[['DeliveryCharges','LateCharges','OtherCharges','OtherChargesDescription',' Amount ','Actual or Estimated']]


# In[ ]:

#Find rows where the sum of Delivery, Other and Late charges != Amount
psET.loc[psET['DeliveryCharges'].astype(float) + psET['LateCharges'].astype(float) + psET['OtherCharges'].astype(float) != psET[' Amount '].astype(float),:]


# In[ ]:

#Fill Service Period nulls with Invoice Date
psET['Service Period'] = psET['Service Period'].fillna(value=psET['Invoice Date'])


# In[ ]:

#Create Start and End Date columns
psET['Start Date'] = ''
psET['End Date'] = ''


# In[ ]:

#For Start and End, have end date be second part of .split('-')
psET['End Date'] = psET['Service Period'].str.split('-').str[-1]


# In[ ]:

#Have start be first part of .split when there is a '-'
psET.loc[psET['Service Period'].str.contains('-'),'Start Date'] = psET['Service Period'].str.split('-').str[0]


# In[ ]:

#start should be End - 30 when there isn't a '-'
temp = pd.to_datetime(psET['End Date']) - timedelta(days=30)
psET.loc[~psET['Service Period'].str.contains('-'),'Start Date'] = temp.astype(str).str.split('-').str[1] + '/' + temp.astype(str).str.split('-').str[2] + '/' + temp.astype(str).str.split('-').str[0]


# In[ ]:

#Establish Bill Month and Bill Year
psET['Bill Month'] = ''
psET['Bill Year'] = ''
psET['End Date']


# In[ ]:

#Find # of days before Start and End Date
psET['temp'] = pd.to_datetime(psET['End Date']) - pd.to_datetime(psET['Start Date'])


# In[ ]:

#When # of days > 45, use the month of the end date
psET.loc[psET['temp'].dt.days > 45,'Bill Month'] = psET['End Date'].str.split('/').str[0]
#When <= 45, use the standard setup
psET.loc[psET['temp'].dt.days <= 45,'Bill Month'] = (pd.to_datetime(psET['End Date']) - pd.to_timedelta(psET['temp'].dt.days/2, unit = 'D')).astype(str).str.split('-').str[1]


# In[ ]:

#same with Bill Year
psET.loc[psET['temp'].dt.days > 45,'Bill Year'] = psET['End Date'].str.split('/').str[2]
psET.loc[psET['temp'].dt.days <= 45,'Bill Year'] = (pd.to_datetime(psET['End Date']) - pd.to_timedelta(psET['temp'].dt.days/2, unit = 'D')).astype(str).str.split('-').str[0]
psET[['Bill Month','Bill Year']]


# In[ ]:

#Bring in EMSYS UoMs
UoM = pd.read_csv(r'C:\Users\HHORNER\Documents\My MTA\Peoplesoft\Current\VendorUoM.csv')
UoM.head()


# In[ ]:

left = psET
right = UoM
peopleSoft = pd.merge(left,right, how='left',on='Vendor Name')
peopleSoft.head()


# In[ ]:

#Check if # of psET rows = # of peopleSoft rows
psET.shape


# In[ ]:

peopleSoft.shape


# In[ ]:

#Add missing UoM's based on Peoplesoft UoM
peopleSoft.loc[peopleSoft['Unit of Measure'] == 'HH','EMSYSUoM'] = 'CCF'
peopleSoft.loc[peopleSoft['Unit of Measure'] == 'GLL','EMSYSUoM'] = 'Gal'
#Check for null UoM
peopleSoft['EMSYSUoM'].isnull().values.any()


# In[ ]:

#Find null UoM
peopleSoft.loc[peopleSoft['EMSYSUoM'].isnull(),:]


# In[ ]:

#Export Water
peopleSoft.loc[peopleSoft['Account Number/Service Type'].str.contains('WATER'),:].to_csv(r'C:\Users\HHORNER\Documents\My MTA\Peoplesoft\Current\PeoplesoftWater.csv')


# In[ ]:

#Export Sewer
peopleSoft.loc[~peopleSoft['Account Number/Service Type'].str.contains('WATER|STEAM'),:].to_csv(r'C:\Users\HHORNER\Documents\My MTA\Peoplesoft\Current\PeoplesoftSewer.csv')


# In[ ]:

#Export Steam
peopleSoft.loc[peopleSoft['Account Number/Service Type'].str.contains('STEAM'),:].to_csv(r'C:\Users\HHORNER\Documents\My MTA\Peoplesoft\Current\PeoplesoftSteam.csv')

