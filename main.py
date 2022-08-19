# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 12:10:31 2022

@author: Afromullet
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import requests
from collections import namedtuple
from os import mkdir
from os import path
from os import rmdir
from os import makedirs
from pathlib import Path
from os.path import exists
import re
import csv
import shutil

#Todo make not global
scraper_info = None

TEST_DIRECTORY = "output_directory" #all test output files go here

#struct_name is name of the structure the case is for. link is the link to the pdf for the case
#Also has a letter_name field so that we can allow only certain letters to be written to a file
Case_Data = namedtuple("Case_Data", "struct_name link letter_name")

#TODO determine when you need to return the Driver and when you can work with just the driver return value
CASES_NUM_CELLS_PER_ROW = 7 #Each case row has 7 cells

cases_headers = ["project_folder","struct_name","link","month_deteremined","full_date"]  #Header for the file keeping track of all downloaded and not cases

#Keeps track of all of the cases that have and haven't been downloaded 
downloaded_cases = "downloaded_cases.csv"
downloaded_cases_file_handle = None

not_downloaded_cases = "not_downloaded_cases.csv"
error_downloading_cases = 'Error downloading.csv' #Files we had a problem downloading


backup_file_string = "backup" 

#Index into this will give us the correct month
months = ["January", "February","March","April","May","June","July","August","September","October","November","December"]
'''
Data class that stores important information we need to traverse the website
'''
class Scraper_Info:
    def __init__(self,login_url,uname,pword,off_airport_url,on_airport_url):
        self.login_url = login_url
        self.uname = uname
        self.pword = pword
        self.off_airport_url = off_airport_url
        self.on_airport_url = on_airport_url
        
'''
A project can have one or more cases.
The Project_Information class contains a list of namedtuples 

Case_Data = namedtuple("Case_Data", "struct_name link letter_name")

A class really should be doing just one thing, but here we both keep the links, create the folders, and write the cases to a file
No need to abstract it more just yet

'''
class Project_Information():
    def __init__(self):
        self.project_name = ""
        self.cases = []
        self.project_folder = None
        self.month_determined = 0 #Month the case was determined
        self.full_date = 0
        
    def add_case_data(self,struct_name,link,letter_name):
        
        '''
        Don't allow \ and / in the struct name. The filename is the struct name, and those will mess with writing to files'
        case.struct_name.replace("/","_")case.struct_name.replace("/","_")
        '''
        
        #Probably don't need the firs twoo string replaces, but for now it works and I don't want to touch it at the moment
        struct_name = struct_name.replace("/","_")
        struct_name = struct_name.replace("\\","_")
        struct_name = ''.join(filter(str.isalnum, struct_name ))
        self.cases.append(Case_Data(struct_name,link,letter_name))
        
    def write_cases_to_folder(self):
        '''Writes all of the cases to a folder.
        '''
        if self.project_folder == None:
            a = 3
            #print("Project folder for " + self.project_name + " Has not been created yet")
        else:
            for case in self.cases:
                
                #Todo handle duplicate names..I.E, Crane, Crane, Crane should be Crane_1,Crane_2,Crane_3
                #Want the file to be stored in the path self.project_name\case.struct_name
                if is_in_downloaded_cases(case):
                    return
    
                #Need to remove special characters in the string because that will cause problem with filewrites
                outfilename = self.project_folder + "\\" + self.full_date + "_" + str(case.struct_name) + ".pdf"
                
                if exists(outfilename):
                    add_to_not_downloaded_cases(self.project_folder,case,self.month_determined,self.full_date)
                    return
                # outfilename = str(case.struct_name) + ".pdf"
                response = requests.get(case.link)
                try:
                    file = open(outfilename, "wb")
                    file.write(response.content)
                    add_to_downloaded_cases(self.project_folder,case)
                    file.close()
                except FileNotFoundError:
                    add_to_error_downloaded_cases(self.project_folder,case)
                    print("error reading file " + outfilename)
                
    def create_folder(self):
        '''
        Creates a folder from a project_information  that uses the project name for the folder name
        todo do error checking to see if the directory is already created
        '''
    
        #Do some checks here to see if the directory was created successfully...but for now, let's just assume it was created and
        #assign the project_name to the project folder
        #also using a test directory for now, remove later
        
        self.project_folder = TEST_DIRECTORY + "\\" + self.month_determined + "\\" + self.project_name
        
        
        if path.exists(self.project_folder) == False:
            makedirs(self.project_folder)
 
        
def add_to_downloaded_cases(project_folder,case):
    
    
    '''Keeps track of all the cases that have been downloaded'''
    
    global downloaded_cases,cases_headers
    
    #Open the file for reading and check if the case already exists
    fh = open(downloaded_cases,"a+",newline="")
    cases_writer = csv.DictWriter(fh,fieldnames=cases_headers)
    cases_writer.writerow({"project_folder":project_folder,"struct_name":case.struct_name,"link":case.link})  
    
def is_in_downloaded_cases(case):
    
    global downloaded_cases
    
    '''
    Checks if the case has already been downloaded
    '''
    fh = open(downloaded_cases,'r')
    
    reader = csv.DictReader(fh)
    
    for row in reader:
        if row['link'] == case.link:
            fh.close()
            return True
        
    fh.close()
    return False
        
def add_to_not_downloaded_cases(project_folder,case,month_determined,full_date):
    
    '''
    Keeps track of all the cases that haven't been downloaded.
    Everytime we run the script, the not downloaded cases starts as an empty file
    
    '''

    global not_downloaded_cases,cases_headers
    
    #Open the file for reading and check if the case already exists
    fh = open(not_downloaded_cases,"a+",newline="")
    cases_writer = csv.DictWriter(fh,fieldnames=cases_headers)
    cases_writer.writerow({"project_folder":project_folder,"struct_name":case.struct_name,"link":case.link,"month_deteremined":month_determined,"full_date" : full_date})   

def add_to_error_downloaded_cases(project_folder,case):
    
    '''Keeps track of the files that had an error when downloading'''
    
    global error_downloading_cases,cases_headers
    
    #Open the file for reading and check if the case already exists
    fh = open(error_downloading_cases,"a+",newline="")
    cases_writer = csv.DictWriter(fh,fieldnames=cases_headers)
    cases_writer.writerow({"project_folder":project_folder,"struct_name":case.struct_name,"link":case.link})         
        
def write_projects_to_folder(all_projects):
    
    for proj in all_projects:
        proj.create_folder()
        proj.write_cases_to_folder()
        
def read_configuration_file():
    login_url, username,password,det_off_aiport,determined_on_airport = "","","","",""
    
    global scraper_info
    '''
    Very basic configuration reading right now. Add error checking todo
    '''
    try:
        # file exists
        with open('conf_file.txt') as cfgfile:
            login_url = cfgfile.readline().split("=")[1].strip()
            username = cfgfile.readline().split("=")[1].strip()
            password = cfgfile.readline().split("=")[1].strip()        
            det_off_aiport = cfgfile.readline().split("=")[1].strip() 
            determined_on_airport = cfgfile.readline().split("=")[1].strip() 
            scraper_info = Scraper_Info(login_url,username,password,det_off_aiport,determined_on_airport)
            return True
            
    except FileNotFoundError:
        print("config file does not exist")
        return False
  
def init_data():
    
    global downloaded_cases_headers,not_downloaded_cases,error_downloading_cases
    
    # #Todo, use a different output directory
    # if path.exists(TEST_DIRECTORY):
    #     rmdir(TEST_DIRECTORY)
        
    # mkdir(TEST_DIRECTORY)
    
    if exists(downloaded_cases) == False:
        fh = open(downloaded_cases,"w+")
        fh.write(cases_headers)
        fh.close()
        
    #thse should be empty files every time we start
    fh = open(not_downloaded_cases,"w")
    cases_writer = csv.DictWriter(fh,fieldnames=cases_headers)
    cases_writer.writeheader()
    fh.close()
    
    fh = open(error_downloading_cases,"w")
    cases_writer = csv.DictWriter(fh,fieldnames=cases_headers)
    cases_writer.writeheader()
    fh.close()
    
def login_to_page():

    global scraper_info #todo make not global
    
    read_configuration_file()
   
    #TODO figure out whether you have to close the driver
    
    chrome_options = Options()

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer-gpu")
    
    driver = webdriver.Chrome(options=chrome_options,service=Service(ChromeDriverManager().install()))
    
    '''Log into the website by looking for the name tag of the HTML that takes the username and password info'''
    driver.get(scraper_info.login_url)
    driver.find_element(By.NAME,"loginForm")
            
    #TODO don't hard code element names
    username_input = driver.find_element(By.NAME,"emanresu")
    password_input = driver.find_element(By.NAME,"drowssap")
    login_button = driver.find_element(By.NAME,"submitButton")
    
    username_input.send_keys(scraper_info.uname)
    password_input.send_keys(scraper_info.pword)
    login_button.click()
    return driver

#TODO need to search both on and off airport construction
def go_to_determined_cases(driver):
    '''
    TODO expand into function that takes as input the link text (I.E, Add Letter, accepted, etc)
    '''
    driver.find_element(By.LINK_TEXT,"Determined").click()

def go_to_url(driver,url):
    driver.get(url)    
    
def get_page_links(driver):
    
    '''
    Get all tags "a" which contins href. We're searching for all links containg "pageNum="
    '''
    pages = []
    link_search_string = "pageNum="
    links = driver.find_elements(By.TAG_NAME,"a")
    
    for l in links:
        href_prop = l.get_property('href')
        if href_prop.find(link_search_string) != -1:
            pages.append(href_prop)
    return list(set(pages)) #Remove duplicates
            
def get_letter_links(driver):
    
    global months
    
    '''
    
    Returns all of the projects from a single page.
    
    Will be a list of Project_Information objects
    
    Iterate over table using a step size that matches the rows length. Each "row" of the loop below will be a row from the cases table
    This gets all of the letter links from a single page, not all of the pages. 
    '''
    dtable = driver.find_element(By.CLASS_NAME,"tableBase")
    dtable = dtable.find_elements(By.CLASS_NAME,"tableCell")
    ROW_LEN = 11
    PROJECT_ROW_INDEX = 3 #Todo find the row index by reading the table header instead of hard coding it
    DATE_DETERMINED_INDEX = 7

    project_list = []
    links_clicked_on_cases_page = 0 #Lets us know if we read all of the cases on the page todo read the cases per page, compare it to this, and report an error if it doesn't match
    for index in range(0,len(dtable),ROW_LEN):

        row = dtable[index:index+ROW_LEN-1]
        project_name = row[PROJECT_ROW_INDEX].text
        
        #Get the month the caqse was determined in so that we can place it in folders sorted by month
        month = row[DATE_DETERMINED_INDEX].text.split("/")[0].strip('0')
        full_date = row[DATE_DETERMINED_INDEX].text.replace("/","_") #Replaces the / with _ so it can be used in a file name

        month_determined = months[int(month)-1] #Subtracting 1 since the month is stored in a list
        
        row[PROJECT_ROW_INDEX].click() #Clicks the link, bringing us to the website where we can access the letter
        links_clicked_on_cases_page += 1 #Keeping track of this for debugging purposes to make sure that we read
        case_table = driver.find_element(By.CLASS_NAME,"tableRowEven")
        case_table_pdf = case_table.find_elements(By.CLASS_NAME,"tableCell")
        #todo find pdf by searching for it rather than using row length
        PDF_INDEX = len(case_table_pdf)
        
        #Checks if we can read the cases by verifying that there is a link
        if case_table_pdf[PDF_INDEX-1].find_elements(By.TAG_NAME,'a'):
            project_list.append(read_all_cases_on_page(driver,project_name,month_determined,full_date))
            
    return project_list
    

def read_all_cases_on_page(driver,project_name,month_determined,full_date):
    
    '''
    
    Returns all of the cases from a single project
    '''
    #Get the table containing the cases and each cell. We will have to iterate over table_rows 
    case_info = driver.find_element(By.CLASS_NAME,"tableBase")
    table_rows = case_info.find_elements(By.CLASS_NAME,'tableCell')
    
    case_list = []
    num_rows_processed = 0 #looks like the i 

        
    project_info = Project_Information()    
    project_info.project_name = project_name
    project_info.month_determined = month_determined
    project_info.full_date = full_date
    if len(table_rows) == CASES_NUM_CELLS_PER_ROW:
  
       
        structure_name = table_rows[0].text.split("\n")[0].strip()
        letter_link = table_rows[CASES_NUM_CELLS_PER_ROW-1].find_element(By.TAG_NAME,'a').get_property('href')
        letter_name = table_rows[CASES_NUM_CELLS_PER_ROW-1].text
        
        project_info.add_case_data(structure_name,letter_link,letter_name)
     
    else:
        
        #We have more than one case on a page, so let's handle that
        for i in range(0,len(table_rows)-CASES_NUM_CELLS_PER_ROW,CASES_NUM_CELLS_PER_ROW):
            try:
      
                structure_name = table_rows[i].text.split("\n")[0].strip()
                letter_link = table_rows[i+CASES_NUM_CELLS_PER_ROW-1].find_element(By.TAG_NAME,'a').get_property('href')
                letter_name = table_rows[i+CASES_NUM_CELLS_PER_ROW-1].text            
                project_info.add_case_data(structure_name,letter_link,letter_name)       
            except NoSuchElementException:
                print("Error reading cases")        
                
        #Get the last case
        num_rows = len(table_rows) - 7
        
        structure_name = table_rows[num_rows].text.split("\n")[0].strip()
        letter_link = table_rows[num_rows+(CASES_NUM_CELLS_PER_ROW-1)].find_element(By.TAG_NAME,'a').get_property('href')
        letter_name = table_rows[CASES_NUM_CELLS_PER_ROW-1].text
        project_info.add_case_data(structure_name,letter_link,letter_name)
       
    driver.back()     
    return project_info

'''
On the project summary page, the first column of each row is the structure name. The string will look something like this:
    
'Tripp WNER900 \nDetermined\n2010-AGL-131-OE', so we split the string by using \n as a delimiter, making the first index the case name.

Making this a function in case we have to do some additional processing and because the get_letter_links is already pretty lonk

'''
def get_structure_name(project_sum_struct_name):
    return project_sum_struct_name.split("\n")[0].strip()

def backup_files():
    global downloaded_cases,not_downloaded_cases,error_downloading_cases,backup_file_string
    
    fname = downloaded_cases.split(".csv")[0] + backup_file_string + ".csv"
    shutil.copyfile(downloaded_cases, fname)
    
    fname = not_downloaded_cases.split(".csv")[0] + backup_file_string + ".csv"
    shutil.copyfile(not_downloaded_cases, fname)

    fname = error_downloading_cases.split(".csv")[0] + backup_file_string + ".csv"
    shutil.copyfile(error_downloading_cases, fname)    
    
    
def get_not_downloaded_cases():
    global not_downloaded_cases
    
    
    '''
        ordered_structs will look like this
        
        {
            {project_name1 : [duplicate file list]},
            {project_name2 : [duplicate file list]},
            {project_nameN : [duplicate file list]}
        }
    
    '''
    ordered_structs = []
    

    file_append_counter = 0

    with open(not_downloaded_cases) as csvfile:
        reader = csv.DictReader(csvfile)
        
        for case in reader:
            ordered_structs.append(case)
 
            # project_name = case["project_folder"].split("\\")[2] #Get the project name after splitting the string. The string is the full directoy

            # # print(struct_name.split("\\"))
            # #The key is the stru
            # if project_name in ordered_structs.keys():
                
            #     for o_case in ordered_structs[project_name]:
                    
            #         #Only append if the link does not already exist
            #         if case["link"] == o_case['link']:
            #             break
            #         else:
            #             ordered_structs[project_name].append(case)
            # else:
            #     ordered_structs[project_name] = [case]
            
    return ordered_structs    


#For every duplicate, increment this by one and append it to the filename.
#Increments it once for every duplicate, not every duplicate with the same struct name
#This will work for now since the numbering really shouldn't matter
def write_not_dowloaded_cases():
    
    duplicate_counter = 0
    not_downloaded = get_not_downloaded_cases()
    
    for case in not_downloaded:
        # outfilename = case["project_folder"] + "\\" +  case["struct_name"] + "__"+ str(duplicate_counter) + ".pdf"
        outfilename = case["project_folder"] +  "__"+ str(duplicate_counter) + ".pdf"
        duplicate_counter += 1
        response = requests.get(case["link"] )
        file = open(outfilename, "wb")
        file.write(response.content)
        file.close()
        print(outfilename)
            
            
def run_script():

    init_data()
    all_letter_links = []
    driver = login_to_page()
    go_to_determined_cases(driver)
    # go_to_url(driver,scraper_info.off_airport_url)
    
    
    pages = get_page_links(driver)
    
    #Gets the index of the = sign, which 
    file_counter = 0
    for p in pages:
    
        projs = get_letter_links(driver) #Cases_list will contain all of the projects from a page    
        write_projects_to_folder(projs)
    
        print("Getting new page")
        driver.get(p)
        print("Got new page")
        
    #Todo check if files and folder have been created already
    #todo try driver.get(p) for certain duration, and if it doesn't work, report which page it failed on
    
    print("Done")
    
    
def get_remaining_cases():

    driver = login_to_page()
    write_not_dowloaded_cases()
    
    
run_script()
# get_remaining_cases()