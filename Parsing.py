import pandas as pd
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
import traceback
from time import sleep

def get_current_time (): #For naming of file in case of exception
    now = datetime.now()
    current_time = now.strftime("%H_%M_%S")
    return current_time


class MyError(Exception): # Custom Error
    def __init__(self, text):
        self.txt = text

#Create DF with generations of cars
df_gens = pd.read_csv('/Users/aleksandrglotov/Desktop/Predict_Youtube_Dislikes/mark_model_generation.csv')

#I this DataFrame we will add all infromation from listing
columns=['listing_id', 'listing_link', 'mark', 'model', 'gen_name', 'year', 'mileage', 'vol_engine', 'fuel', 'price', 'region', 'title', 'sub_title']
df_listings=pd.DataFrame(columns=columns)

#Masks for generations links
mask_link='https://www.otomoto.pl/osobowe/{}/{}/?search%5Bfilter_enum_damaged%5D=0&'
mask_gen_filter='?search%5Bfilter_enum_generation%5D={}'

while True: #Loop from checkpoint

    # Create seleium Chrome driver for parsing
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(chrome_options=chrome_options)

    #In case of problems create chekpoint
    check_point_df=pd.read_csv('Checkpoint.csv')
    points=check_point_df.values[-1]
    print(points)
    gen_n=points[1]
    gen_n_p=points[2]


    try: #In case of problem Exception save current data to csv, next time we start from this place

        for gen in df_gens.values[gen_n:]:
            print(gen)
            mark=gen[1]
            model=gen[2]
            gen_name=str(gen[3])#Str because it can't be None in future
            print(gen_name)
            if gen_name=='nan': #We creating links depends of availability generations
                link=mask_link.format(mark,model)
            else:
                link=mask_link.format(mark,model)+mask_gen_filter.format(gen_name)
            # print(link)

            driver.get(link) #Get page
            sleep(1)

            #Push button accept if it possible
            try:
                elem = driver.find_element(By.ID, 'onetrust-accept-btn-handler')
                elem.click()
            except:
                print('No accept button')

            #Find how many pages we have in genereation
            #First find number of lisitngs of this generations
            n_pages=driver.find_element(By.XPATH,'/html/body/div[1]/div/div/div/div[2]/div[2]/div[2]/div[1]/div[3]/div[1]/div[1]/a[1]').text
            #Coverte it to int
            n_pages=re.findall('Wszystkie \((.+)\)',n_pages)[0].replace(' ','')
            #We know that we have 32 listings on our page
            n_pages=int(n_pages)//32+1

            #Now we visite each page and find all listings on page


            for p in range(gen_n_p,n_pages):
                sleep(1)
                if p>1: #Actually we e are already on page N1
                    link_p = link + '&page={}'.format(p)
                    driver.get(link_p)
                sleep(1)
                #Find all listing's blocks
                listings = driver.find_elements(By.XPATH,
                                                '/html/body/div[1]/div/div/div/div[2]/div[2]/div[2]/div[1]/div[3]/main/article')

                #If we have DF we load it
                try:
                    df_listings=pd.read_csv('general_data_frame.csv')
                    # print('opened general file')
                except Exception as e:
                    print(f'general file not found\b{e}')

                #Create checkpoint and save it
                df_point = pd.DataFrame()
                checkpoint = [[gen[0],p]]
                df_point[['genereation', 'page']] = checkpoint
                df_point.to_csv('Checkpoint.csv')

                #Now we can find informations in our blocks
                n = 0
                gen_n_p = 1

                if len(listings)==0:
                    raise MyError('Listings list is empty')


                for i in listings:
                    n += 1
                    price= i.find_element(By.CLASS_NAME, 'optimus-app-epvm6').text  # Price
                    title=i.find_element(By.CLASS_NAME, 'e1b25f6f13').text # Title
                    sub_title=i.find_element(By.CLASS_NAME, 'e1b25f6f7').text # Subtitle
                    #Region:
                    region= i.find_element(By.XPATH,
                                                   f'/html/body/div[1]/div/div/div/div[2]/div[2]/div[2]/div[1]/div[3]/main/article[{n}]/div[1]/p').text
                    #Year, milage, volume of engine and engine type
                    other_data = i.find_element(By.XPATH,
                                                f'/html/body/div[1]/div/div/div/div[2]/div[2]/div[2]/div[1]/div[3]/main/article[{n}]/div[1]/div/ul').text.split(
                        '\n')

                    year=other_data[0]
                    mileage=other_data[1]

                    #If we have electric car we don't have volume of engine so we have to check it
                    if len(other_data)==4:
                        vol_engine=other_data[2]
                        fuel=other_data[3]
                    elif len(other_data) == 3:
                        vol_engine = 0
                        fuel = other_data[2]
                    elif len(other_data) == 2:
                        vol_engine = 0
                        fuel = other_data[1]
                        mileage = 0

                    #Link to listing with full description
                    listing_link=i.find_element(By.XPATH,
                                         f'/html/body/div[1]/div/div/div/div[2]/div[2]/div[2]/div[1]/div[3]/main/article[{n}]/div[1]/h2/a').get_attribute(
                        'href')
                    listing_id =i.get_attribute('id') #Listing id

                    #We have to check type of link because some listings are ad and show us wrong information
                    if 'klik' not in listing_link and 'carsmile' not in listing_link:
                        #Format date for DF
                        listing_data=[listing_id,listing_link,mark,model,gen_name,year,mileage,vol_engine,fuel,price,region,title,sub_title]
                        #Add lineinto DF
                        df_listings.loc[len(df_listings)]=listing_data
                    else:
                        print(f"Don't add {title}\nLink:{listing_link}\bOur model is {model}")
                #Save DataFrame and create if it isn't exist. In case of error we don't lost information and start from place of error
                df_listings.to_csv('general_data_frame.csv',index=False)

                if gen[0]==len(df_gens): #Stop loop
                    break


    except Exception as e: # In case of error we save current DF also here we can check error
        print(traceback.format_exc()) #Print error
        # df_listings.to_csv(f'reserves/reserve_save_{get_current_time()}') #Backup Save
        driver.close()  # Close selenium driver


