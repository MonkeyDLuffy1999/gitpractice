# --------------------- IMPORTS ---------------------
# Import dynamics.csv containing all active residents in D365 for all sites
# Import ecase.csv containing all active residents in eCase for all sites
# Import salesforce.csv containg all sale records in Salesforce for specific sites. Below is an example
# ('Arcare Glenhaven', 'Arcare Taigum', 'Arcare Keysborough', 'Arcare Nirvana', 'Arcare Parkview Malvern East')

import pandas as pd

dynamics = pd.read_csv('dynamics.csv')
ecase = pd.read_csv('ecase.csv')
salesforce = pd.read_csv('salesforce.csv')
#ecase[ecase['id'] == 16917]

ecase.head()


# Updating discrepency in salesforce records
#salesforce[salesforce['Id'] == '0064U00000m4FYEQA2']

# --------------------- DYNAMICS CLEANING ---------------------

# Clean dynamics to have required columns below
# 'Account', 'First name', 'Last name', 'Service description', 'Place', 'Entry date'
# 'Statement preference', 'Email address', 'Phone', 'ADDIT FEES', 'TELERENTAL'

dynamics_dc = dynamics[['Account', 'First name', 'Last name', 'Service description', 'Place', 'Entry date','Statement preference', 'Email address', 'Phone', 'ADDIT FEES', 'TELERENTAL']]
# Renaming columns appropriately
dynamics_dc = dynamics_dc.rename(columns={
    'Account': 'id',
    'First name': 'firstname',
    'Last name': 'lastname',
    'Service description': 'residence',
    'Entry date': 'admission_date',
    'Email address': 'billing_email',
    'Phone': 'billing_phone',
    'ADDIT FEES': 'as_fees',
    'TELERENTAL': 'telephone_fees',
    'Statement preference': 'billing_method',
    'Place': 'room'
})

# Changes First Name to first_name
dynamics_dc.columns = dynamics_dc.columns.str.lower().str.replace(' ', '_')
#dynamics = dynamics.add_suffix('_dy')
#dynamics_dc.head()

# --------------------- DYNAMICS TRANSFORMATION ---------------------

# Create bed to store A and B for two beds in a single room
# Update room with 3 digit room number only from ARAN001, BELM013, ARAN121 to 001, 013, 121 etc.
# Update with correct data types

dynamics_dt = dynamics_dc

# Extract 3 digit from room (060 from Room060A) and update room with this value
dynamics_dt['room'] = dynamics_dc['room'].str.extract(r'(\d{3})')

# Extract last string (A from Room060A) and store in room letter. Then create bed column to store Room number + last letter i.e. 010A
room_letter = dynamics_dc['room'].str.extract(r'([A-Za-z])$').fillna('')
dynamics_dt.insert(5,'bed', dynamics_dt['room'] + room_letter[0].str.upper())

# To date
dynamics_dt['admission_date'] = pd.to_datetime(
    dynamics_dc['admission_date'],
    format='%d/%m/%Y',
    errors='coerce'
)

# To category
cat_cols = ['residence', 'billing_method']
for col in cat_cols:
    dynamics_dt[col] = dynamics_dc[col].astype('category')

dynamics_dt['residence'] = dynamics_dt['residence'].str.title().str.strip()
dynamics_dt['firstname'] = dynamics_dt['firstname'].str.title().str.strip()
dynamics_dt['lastname'] = dynamics_dt['lastname'].str.title().str.strip()

# To string
dynamics_dt['id'] = dynamics_dc['id'].astype('string')

# To numeric downcast
dynamics_dt['as_fees'] = pd.to_numeric(dynamics_dc['as_fees']).fillna('')
dynamics_dt['telephone_fees'] = pd.to_numeric(dynamics_dc['telephone_fees'], downcast='float').fillna('')

# Filter records for required residences below
# ('Arcare Glenhaven', 'Arcare Taigum', 'Arcare Keysborough', 'Arcare Nirvana', 'Arcare Parkview Malvern East')
# Filter records for admission_date < '01/11/2025'

#dynamics_dt = dynamics_dt[dynamics_dt['residence'].isin(['Arcare Glenhaven', 'Arcare Taigum', 'Arcare Keysborough', 'Arcare Nirvana', 'Arcare Parkview Malvern East'])]
dynamics_dt = dynamics_dt.sort_values(by=['residence', 'admission_date'], ascending = [True, False])
dynamics_dt = dynamics_dt[dynamics_dt['admission_date'] < pd.Timestamp('2025-11-01')].reset_index(drop=True)

# --------------------- DYNAMICS DATA LOAD ---------------------
# Show up to 100 rows
pd.set_option('display.max_rows', None)

# Sorting for analysis
dynamics_sorted = dynamics_dt.sort_values(by=['residence', 'room'], ascending = [True, True]).reset_index(drop=True)

# Picking Glenhaven to start with
#dynamics_glen = dynamics_sorted[dynamics_sorted['residence'] == 'Arcare Burnside']


dynamics_glen = dynamics_sorted

#dynamics_glen.info()
dynamics_glen[dynamics_glen['firstname'] == 'Dyson']

# --------------------- ECASE CLEANING ---------------------
# Keep only required columns below
# ['id', 'Customer_Code', 'TrustCustomer_Code', 'firstname', 'lastname', 'DateOfBirth', 'medicarenum', 'facilityname', 'accomentrydate', 'roomdescription', 'beddescription']

# Create list of columns to keep
cols = ['id', 'Customer_Code', 'TrustCustomer_Code', 'firstname', 'lastname', 'DateOfBirth', 'medicarenum', 'facilityname', 'accomentrydate', 'roomdescription', 'beddescription']

# Assign columns to keep
ecase_dc = ecase[cols]

# Rename those columns
ecase_dc = ecase_dc.rename(columns={
    'Customer_Code': 'code',
    'TrustCustomer_Code': 'dynamics_id',
    'DateOfBirth': 'dob',
    'medicarenum': 'medicare',
    'facilityname': 'residence',
    'accomentrydate': 'admission_date',
    'roomdescription': 'room',
    'beddescription': 'bed'
})

ecase_dt = ecase_dc


# Parkview data discrepency, DYSON HORE-LACY
ecase_dt.loc[ecase_dt['firstname'] == 'Dyson', 'lastname'] = 'Hore-Lacy'

ecase_dt.head()

# --------------------------ECASE TRANSFORMATION------------------------------

# Update room with 3 digit room number only from Room 018, Room009 to 018, 009 etc.
# Update with correct data types

ecase_dt['room'] = ecase_dt['room'].astype('string')
ecase_dt['bed'] = ecase_dt['bed'].astype('string')

# ROOM: extract digits and pad to 3 digits
ecase_dt['room'] = ecase_dt['room'].str.extract(r'(\d+)')
ecase_dt['room'] = ecase_dt['room'].str.zfill(3)

# BED: extract digits and optional trailing letter
bed_digits = ecase_dt['bed'].str.extract(r'(\d+)')
bed_letter = ecase_dt['bed'].str.extract(r'([A-Za-z])$').fillna('')

# combine padded digits + letter
ecase_dt['bed'] = bed_digits[0].str.zfill(3) + bed_letter[0].str.upper()
# To date
ecase_dt['dob'] = pd.to_datetime(
    ecase_dt['dob'],
    format='%d/%m/%Y',
    errors='coerce'
)

ecase_dt['admission_date'] = pd.to_datetime(
    ecase_dt['admission_date'],
    format='%d/%m/%Y',
    errors='coerce'
)

# To category
ecase_dt['residence'] = ecase_dc['residence'].astype('category')
# To title case
ecase_dt['residence'] = ecase_dt['residence'].str.title().str.strip()
ecase_dt['firstname'] = ecase_dt['firstname'].str.title().str.strip()
ecase_dt['lastname'] = ecase_dt['lastname'].str.title().str.strip()


# To string
ecase_dt['id'] = ecase_dc['id'].astype('string')
ecase_dt['code'] = ecase_dc['code'].astype('string')
ecase_dt['dynamics_id'] = ecase_dc['dynamics_id'].astype('string')

ecase_dt.head()

# Filter records for required residences below
# ('Arcare Glenhaven', 'Arcare Taigum', 'Arcare Keysborough', 'Arcare Nirvana', 'Arcare Parkview Malvern East')
# Filter records for admission_date < '01/11/2025'

ecase_dt = ecase_dt[ecase_dt['admission_date'] < pd.Timestamp('2025-11-01')].reset_index(drop=True)
#ecase_dt = ecase_dt[ecase_dt['residence'].isin(['Arcare Glenhaven', 'Arcare Taigum', 'Arcare Keysborough', 'Arcare Nirvana', 'Arcare Parkview Malvern East'])]
ecase_dt.info()

# ----------------------------ECASE DATA LOAD----------------------------------

# Sorting for analysis
ecase_sorted = ecase_dt.sort_values(by=['residence', 'room'], ascending = [True, True]).reset_index(drop=True)

# Picking Glenhaven to start with
#ecase_glen = ecase_sorted[ecase_sorted['residence'] == 'Arcare Burnside'].reset_index(drop=True)

ecase_glen = ecase_sorted

ecase_glen.info()

# ----------------------------------------- DYNAMICS AND ECASE DATA MERGE -----------------------------------------------
# Add Suffixes as dy for dynamics and ec for ecase before merge

# Add Suffixes as dy for dynamics and ec for ecase before merge
dynamics_glen = dynamics_glen.add_suffix('_dy')
ecase_glen = ecase_glen.add_suffix('_ec')

# First LEFT MERGE ecase_glen to dynamics_glen on room_ec = room_dy. Then drill down further as there could be multiple beds in one room creating duplicate records in merged df, or no match at all
ecase_dynamics_room_merged = ecase_glen.merge(
    dynamics_glen[['id_dy','firstname_dy', 'lastname_dy', 'room_dy', 'bed_dy', 'billing_method_dy','billing_email_dy','as_fees_dy','telephone_fees_dy']],
    left_on = ['room_ec', 'lastname_ec'],
    right_on = ['room_dy', 'lastname_dy'],
    how = 'left'
)
ecase_dynamics_room_merged.info()

# There are duplicates which needs to be dealt if below return any records
# ecase_dynamics_room_merged[ecase_dynamics_room_merged.duplicated(keep=False, subset=['id_ec'])]


# 1. create a firstname unmatched flag to filter out multiple bed duplicates. Here, mismatch column to record duplicates with unmatched first names as true
# KEEP IN MIND ALL DYNAMICS IDS IN ECASE ARE NOT CORRECT, hence FIRSTNAME MIGHT NEED TO BE USED

# identify duplicates with filter unmatched firstname from ecase and dynamics
ecase_dynamics_room_merged['mismatched_firstname'] = (ecase_dynamics_room_merged.duplicated(keep=False, subset=['id_ec']))  & (ecase_dynamics_room_merged['firstname_ec'] != ecase_dynamics_room_merged['firstname_dy'])
#ecase_dynamics_room_merged[ecase_dynamics_room_merged['mismatched_firstname']]

# 2. Returning true should be dropped
ecase_dynamics_room_merged_dup_removed = ecase_dynamics_room_merged[~ecase_dynamics_room_merged["mismatched_firstname"]].reset_index(drop=True)

ecase_dynamics_room_merged_dup_removed[ecase_dynamics_room_merged_dup_removed['id_dy'].isna()]

# Find duplicated rows based on id_ec, as there are residents with same room number because of double bed. These duplicated ones to be removed using comparision on dynamics_id_ec and id_dy or firstname_ec = firstname_dy

# Create second ecase left merge with dynamics on firstname and lastname to combine this with first merge above for missing record
ecase_dynamics_name_merged = ecase_glen.merge(
    dynamics_glen[['id_dy','firstname_dy', 'lastname_dy', 'room_dy', 'bed_dy', 'billing_method_dy','billing_email_dy','as_fees_dy','telephone_fees_dy']],
    left_on = ['firstname_ec', 'lastname_ec'],
    right_on = ['firstname_dy', 'lastname_dy'],
    how = 'left'
)
ecase_dynamics_name_merged[ecase_dynamics_name_merged['id_dy'].isna()]

# identify duplicates with filter unmatched firstname from ecase and dynamics
ecase_dynamics_name_merged['mismatched_firstname'] = (ecase_dynamics_name_merged.duplicated(keep=False, subset=['id_ec']))  & (ecase_dynamics_name_merged['firstname_ec'] != ecase_dynamics_name_merged['firstname_dy'])
#ecase_dynamics_room_merged[ecase_dynamics_room_merged['mismatched_firstname']]

# 2. Returning true should be dropped
ecase_dynamics_name_merged_dup_removed = ecase_dynamics_name_merged[~ecase_dynamics_name_merged["mismatched_firstname"]].reset_index(drop=True)

ecase_dynamics_name_merged_dup_removed[ecase_dynamics_name_merged_dup_removed['id_dy'].isna()]

#Now Combine room merge and name merge to fill missing records
ecase_dynamics_merge_combined = ecase_dynamics_room_merged_dup_removed.combine_first(ecase_dynamics_name_merged_dup_removed)

# ------------------------------------ DYNAMICS AND ECASE MERGED DATA LOAD ------------------------------------------

# Keep required columns only and order them
cols = ['residence_ec','id_ec', 'code_ec', 'dynamics_id_ec', 'id_dy', 'firstname_ec','firstname_dy', 'lastname_ec', 'lastname_dy',
       'dob_ec', 'admission_date_ec', 'room_ec',  'room_dy',
       'bed_ec', 'bed_dy', 'billing_method_dy',
       'billing_email_dy', 'as_fees_dy', 'telephone_fees_dy']

ecase_dynamics_final = ecase_dynamics_merge_combined[cols]

ecase_dynamics_final.head()
ecase_dynamics_final[ecase_dynamics_final['id_dy'].isna()]

# ---------------------------------- SALESFORCE DATA CLEANING -----------------------------------
salesforce_dc = salesforce
#salesforce.groupby('Residence__r.Name').count()

salesforce_dc.info()
#salesforce_dc.groupby('Residence__r.Name').size()

# Clean room_bed_number_c like 1, 01A, Room1 etc. Filter and title case, Change Data type

# Keep only sale records with latest Date_of_Entry__c
salesforce_dc = (
    salesforce_dc
    .sort_values(
        by=['Residence__r.Name', 'Resident_Name__c', 'Date_of_Entry__c'],
        ascending=[True, True, False]   # latest date first
    )
    .drop_duplicates(subset='Resident_Name__c', keep='first')
    .reset_index(drop=True)
)

# Create room column to keep 3 digit room number only
salesforce_dc['room'] = salesforce_dc['Room_Bed_Number__c'].str.extract(r'(\d+)')  # extract digits
salesforce_dc['room'] = salesforce_dc['room'].str.zfill(3)           # pad with zeros

# Create bed column to keep 3 digit + last string if any
# Extract trailing letter if present
bed_letter = salesforce_dc['Room_Bed_Number__c'].str.extract(r'([A-Za-z])$')[0].str.upper().fillna('')
salesforce_dc['bed'] = salesforce_dc['room'] + bed_letter

# Title case 
salesforce_dc['Resident_Name__r.FirstName'] = salesforce_dc['Resident_Name__r.FirstName'].str.title().str.strip()
salesforce_dc['Resident_Name__r.LastName'] = salesforce_dc['Resident_Name__r.LastName'].str.title().str.strip()
salesforce_dc['Residence__r.Name'] = salesforce_dc['Residence__r.Name'].str.title().str.strip()

# To date
salesforce_dc['Date_of_Entry__c'] = pd.to_datetime(
    salesforce_dc['Date_of_Entry__c']
)

salesforce_dc['DOB__c'] = pd.to_datetime(
    salesforce_dc['DOB__c'],
    format='%d/%m/%Y',
    errors='coerce'
)

# To category
salesforce_dc['Residence__r.Name'] = salesforce_dc['Residence__r.Name'].astype('category')

# ------------------------ SALESFORCE TRANSFORMATION---------------------
#Keep required columns only, order and rename them

salesforce_dt = salesforce_dc

sf_cols = ['Id', 'Resident_Name__c', 'Resident_Name__r.FirstName',
       'Resident_Name__r.LastName', 'DOB__c',
       'Date_of_Entry__c', 'Medicare_Number__c', 'Residence__r.Name', 'room',
       'bed']

salesforce_dt = salesforce_dt[sf_cols]
salesforce_dt = salesforce_dt.rename(columns={
                                    'Id': 'saleId',
                                    'Resident_Name__c': 'residentId',
                                    'Resident_Name__r.FirstName': 'firstname',
                                    'Resident_Name__r.LastName': 'lastname',
                                    'DOB__c': 'dob',
                                    'Date_of_Entry__c': 'admission_date',
                                    'Medicare_Number__c': 'medicare',
                                    'Residence__r.Name': 'residence'
})

salesforce_dt = salesforce_dt.add_suffix('_sf')
salesforce_dt[salesforce_dt['saleId_sf'].isin(['006QK000005bU4HYAU','0064U00000pGO66QAG','006QK00000HpNSEYA3'])]

# -------------------------- SALESFORCE DATA LOAD ------------------------------


#salesforce_glen = salesforce_dt[salesforce_dt['residence_sf'] == 'Arcare Burnside']

salesforce_glen = salesforce_dt


#salesforce_glen[salesforce_glen['admission_date_sf'] == '2023-12-20']
#salesforce_glen.sort_values(by='room_sf')

# ---------------------- FINAL MERGE ----------------------------

ecase_dynamics_final.info()
ecase_dynamics_final.head()

# Left merge ecase_dynamics_final and salesforce_glen on dob and lastname. But this will have missing values on salesforce_glen as not all will match
final_dob_lname = ecase_dynamics_final.merge(
    salesforce_glen[['residence_sf','saleId_sf', 'firstname_sf', 'lastname_sf', 'room_sf','bed_sf','dob_sf','admission_date_sf']],
    left_on = ['residence_ec', 'dob_ec', 'lastname_ec'],
    right_on = ['residence_sf','dob_sf', 'lastname_sf'],
    how = 'left'
)

pd.set_option('display.max_columns', None)

# Check to see if any duplicates 
#final_dob_lname[final_dob_lname.duplicated(subset = ['id_ec'], keep=False)]

# check to see unmatched
final_dob_lname[final_dob_lname['saleId_sf'].isna()]

# Left merge ecase_dynamics_final and salesforce_glen on admission_date and firstname. But this will have missing values on salesforce_glen as not all will match
final_doe_fname = ecase_dynamics_final.merge(
    salesforce_glen[['residence_sf','saleId_sf', 'firstname_sf', 'lastname_sf', 'room_sf','bed_sf','dob_sf','admission_date_sf']],
    left_on = ['residence_ec','admission_date_ec', 'firstname_ec'],
    right_on = ['residence_sf','admission_date_sf', 'firstname_sf'],
    how = 'left'
)
#final_doe_fname.info()

# Check to see if any duplicates 
#final_doe_fname[final_doe_fname.duplicated(subset = ['id_ec'], keep=False)]

# check to see unmatched
final_doe_fname[final_doe_fname['saleId_sf'].isna()]

# Left merge ecase_dynamics_final and salesforce_glen on admission_date and firstname. But this will have missing values on salesforce_glen as not all will match
final_room_fname = ecase_dynamics_final.merge(
    salesforce_glen[['residence_sf','saleId_sf', 'firstname_sf', 'lastname_sf', 'room_sf','bed_sf','dob_sf','admission_date_sf']],
    left_on = ['residence_ec','room_ec', 'lastname_ec','dob_ec'],
    right_on = ['residence_sf','room_sf', 'lastname_sf','dob_sf'],
    how = 'left'
)
#final_room_fname.info()

# Check to see if any duplicates 
#final_room_fname[final_room_fname.duplicated(subset = ['id_ec'], keep=False)]

# check to see unmatched
final_room_fname[final_room_fname['saleId_sf'].isna()]

#resetting index
final_dob_lname = final_dob_lname.reset_index(drop=True)
final_doe_fname = final_doe_fname.reset_index(drop=True)

# Now combine above two merges to fill in null values. This keeps columns from final_dob_lname only as they both have same columns
final_merged1 = final_dob_lname.combine_first(final_doe_fname)

# Keep only required columns and re order
final_merged1 = final_merged1[['residence_ec','residence_sf','saleId_sf', 'id_ec', 'code_ec', 'id_dy', 'dynamics_id_ec', 
                             'firstname_ec', 'firstname_dy', 'firstname_sf', 
                             'lastname_ec', 'lastname_dy',  'lastname_sf',
                             'dob_ec', 'dob_sf', 
                             'admission_date_ec', 'admission_date_sf',
                             'room_ec', 'room_dy', 'room_sf', 
                             'bed_ec', 'bed_dy', 'bed_sf',
                             'billing_method_dy', 'billing_email_dy', 'as_fees_dy', 'telephone_fees_dy'
                             ]]



#final_merged1[final_merged1.duplicated(subset = ['id_ec'], keep=False)]

final_merged1[final_merged1['saleId_sf'].isna()]

#resetting index
final_merged1 = final_merged1.reset_index(drop=True)
final_room_fname = final_room_fname.reset_index(drop=True)

# Now combine above two merges to fill in null values. This keeps columns from final_dob_lname only as they both have same columns
final_merged2 = final_merged1.combine_first(final_room_fname)

# Keep only required columns and re order
final_merged2 = final_merged2[['residence_ec','residence_sf',
                               'saleId_sf', 'id_ec', 'code_ec', 'id_dy', #'dynamics_id_ec', 
                             'firstname_ec', 'firstname_dy', 'firstname_sf', 
                             'lastname_ec', 'lastname_dy',  'lastname_sf',
                             #'dob_ec', 'dob_sf', 
                             'admission_date_ec', 'admission_date_sf',
                             'room_ec', 'room_dy', 'room_sf', 
                             #'bed_ec', #'bed_dy', 'bed_sf',
                             'billing_method_dy', 'billing_email_dy', 'as_fees_dy', 'telephone_fees_dy'
                             ]]

len(final_merged2[final_merged2['saleId_sf'].isna()])

final_merged2[
    (final_merged2['id_dy'].isin(['RES0035962','RES0032507','RES0031057'])) 
    & 
    (final_merged2['saleId_sf'].isna())
]

# ---------------------------------------------------- FINAL ANALYSIS ----------------------------

# Check null values in salesId_sf to see if any with unmatched result
#final_merged2.info()

# Check if firstname on ecase - salesforce and dynamics - salesforce does not match. Just to make sure wrong residents have not been merged
final_merged2[(final_merged2['firstname_ec'] != final_merged2['firstname_sf']) | (final_merged2['firstname_dy'] != final_merged2['firstname_sf'])]

# ---------------------------------------------- FINAL DATA EXPORT ---------------------------------------------

# Rename column to match salesforce upload
final_output = final_merged2.rename(columns={
        'residence_ec': 'residence_ec',
        'residence_sf': 'residence_sf',
        'saleId_sf': 'id',
        'id_ec': 'eCaseId__c', 
        'code_ec': 'eCase_code__c', 
        'id_dy': 'DynamicsID__c',
        'room_ec': 'eCase_bed__c', 
        'billing_method_dy': 'Billing_method__c',
        'billing_email_dy': 'Dynamics_billing_email_address__c',
        'as_fees_dy': 'Old_Additional_Service_Fee_from_Dynamics__c',
        'telephone_fees_dy': 'Old_Monthly_Telephone_Fee_from_Dynamics__c'
})

# Add uploadid and recordtype
final_output['uploadid__c'] = 'FINAL-13/04'
final_output['recordtypeid'] = '012QK000001UzVJYA0'

#final_output.columns
final_output = final_output[['residence_ec','residence_sf','admission_date_ec','firstname_ec','lastname_ec',
                             'id', 'eCaseId__c', 'eCase_code__c', 'DynamicsID__c', 'eCase_bed__c',
       'Billing_method__c', 'Dynamics_billing_email_address__c',
       'Old_Additional_Service_Fee_from_Dynamics__c',
       'Old_Monthly_Telephone_Fee_from_Dynamics__c', 'uploadid__c',
       'recordtypeid']].reset_index(drop=True)

final_output.info()

final_output.to_csv('sf_upload_2ndlot.csv', index=False)