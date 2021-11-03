#This script scrapes the recreation.gov website for campsite availability in Yosemite
#If a campsite is found, a text is sent along with a unique code, and the campsite is held for 15 minutes
#If you respond to the text using the unique code, the script will automatically book the campsite for you

from selenium import webdriver
import smtplib
import imaplib
import email
import sys
import time
import datetime
import random

#Dates must be in this exact form: 'Tue Apr 10 2018'
arrival_date='Tue Apr 10 2018'
depart_date='Wed Apr 11 2018'

#Gmail to send notifications from
gmail_address = ''
gmail_password = ''

#Send notifications to a verizon phone number
verizon_phone_address = '0000000000@vtext.com'

#Login to recreation.gov and book the campsite with these details
recreation_email = ''
recreation_password = ''
credit_card_number = ''
security_code = ''
expire_month = ''
expire_year = ''
first_name = ''
last_name = ''


campground_URLs = [ 'https://www.recreation.gov/camping/upper-pines/r/campsiteSearch.do?site=all&type=9&minimal=no&search=site&contractCode=NRSO&parkId=70925', #Upper Pines
                    'https://www.recreation.gov/camping/lower-pines/r/campsiteSearch.do?site=all&type=9&minimal=no&search=site&contractCode=NRSO&parkId=70928', #Lower Pines
                    'https://www.recreation.gov/camping/north-pines/r/campsiteSearch.do?site=all&type=9&minimal=no&search=site&contractCode=NRSO&parkId=70927' ] #North Pines
                    #'https://www.recreation.gov/camping/tuolumne-meadows/r/campsiteSearch.do?site=all&type=9&minimal=no&search=site&contractCode=NRSO&parkId=70926' #Tuolumne Meadows
                    
path_to_chromedriver = 'C:\Python27\Scripts\chromedriver.exe' # change path as needed

class campsite:
    def __init__(self, campground, site_number, site_type, max_people, handicapped):
        self.campground = campground
        self.site_number = site_number
        self.site_type = site_type
        self.max_people = max_people
        self.handicapped = handicapped
    def __str__(self):
        return self.campground + ' ' + self.site_number + ' ' + self.site_type + ' ' + self.max_people + ' ' + str(self.handicapped)

#Function to clear the pop-up on recreation.gov
def pop_up():
    try:
        browser.find_element_by_xpath('//*[@id="acsMainInvite"]/a').click()
    except:
        x=1

#Send an email from gmail
def send_email(toaddrs, subject, body):
    fromaddr = gmail_address
    msg = "\r\n".join([
      "From: %s" % fromaddr,
      "To: %s" % toaddrs,
      "Subject: %s" %subject,
      "",
      "%s" % body
      ])
    username = gmail_address
    password = gmail_password
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(username,password)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()

#Read the From, Subject, and DateTime fields from the latest email in gmail
def read_email():
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(gmail_address,gmail_password)
    mail.select('inbox')

    type, data = mail.search(None, 'ALL')
    mail_ids = data[0]
    id_list = mail_ids.split()
    latest_email_id = int(id_list[-1])

    typ, data = mail.fetch(latest_email_id, '(RFC822)')
    for response_part in data:
        if isinstance(response_part, tuple):
            msg = email.message_from_string(response_part[1])
            email_subject = msg['subject']
            email_from = msg['from']
            email_date = msg['received']
            email_date = email_date.split(";")[1].lstrip()
            email_datetime = datetime.datetime.strptime(email_date, '%a, %d %b %Y %H:%M:%S -0700 (PDT)')
    return email_from, email_subject, email_datetime

#Check if the email is less than 15 minutes old, has the correct subject, and is from the correct address
def check_email_valid(email_from, email_subject, email_time, check_number):
    current_time = datetime.datetime.now()
    time_difference = current_time - email_time
    if time_difference.total_seconds() < 900:
        if email_subject == "Book " + check_number:
            if email_from == verizon_phone_address:
                print "Everything matches. Book it!"
                return True
            else:
                print "Email address doesn't match"
        else:
            print "Email subject doesn't match"
    else:
        print "No emails in the last 15 minutes"
    return False


for k in range(len(campground_URLs)):
    #Open crome browser to recreation.gov using chromedriver
    browser = webdriver.Chrome(executable_path = path_to_chromedriver)
    browser.set_window_size(1600,900) #If the browser is too narrow, recreation.gov formats everything differently
    url = campground_URLs[k]
    browser.get(url)


    #Set the arrival and departure dates, then click the search button
    arrival_box = browser.find_element_by_xpath('//*[@id="arrivalDate"]')
    arrival_box.click()
    arrival_box.send_keys(arrival_date)
    depart_box = browser.find_element_by_xpath('//*[@id="departureDate"]')
    depart_box.click()
    depart_box.send_keys(depart_date)
    browser.find_element_by_xpath('//*[@id="filter"]').click()


    #Create array of all available campsites
    sites=[]
    for i in range(1, 26):
        available_button = browser.find_element_by_xpath('//*[@id="shoppingitems"]/tbody/tr['+str(i)+']/td[7]/a')
        available = available_button.get_attribute('class')
        if available == "book now":
            campground = browser.find_element_by_xpath('//*[@id="shoppingitems"]/tbody/tr['+str(i)+']/td[2]').text
            site_number_element = browser.find_element_by_xpath('//*[@id="shoppingitems"]/tbody/tr['+str(i)+']/td[1]')
            site_number = site_number_element.find_element_by_class_name('siteListLabel').text
            site_type = browser.find_element_by_xpath('//*[@id="shoppingitems"]/tbody/tr['+str(i)+']/td[3]').text
            max_people = browser.find_element_by_xpath('//*[@id="shoppingitems"]/tbody/tr['+str(i)+']/td[4]').text
            try:
                handicapped_element = browser.find_element_by_xpath('//*[@id="shoppingitems"]/tbody/tr['+str(i)+']/td[4]/img')
                print handicapped_element.get_attribute('title')
                if handicapped_element.get_attribute('title') == "Accessible":
                    handicapped = True
                else:
                    handicapped = False
            except:
                handicapped = False
            sites.append(campsite(campground, site_number, site_type, max_people, handicapped))
            print sites[i-1]
        else:
            break
        print available
        
    #Check if any sites are available
    if len(sites) > 0:
        pop_up()
        print "Campsites Available!"

        #If more than one site is available, choose the best one
        chosen_site = 0
        for i in range(len(sites)):
            if (sites[i].site_type == "STANDARD NONELECTRIC" or sites[i].site_type == "TENT ONLY NONELECTRIC") and sites[i].handicapped == False:
                chosen_site = i
        print i
        print sites[chosen_site]
        pop_up()
        browser.find_element_by_xpath('//*[@id="shoppingitems"]/tbody/tr['+str(chosen_site+1)+']/td[7]/a').click()
        time.sleep(10)
        pop_up()
        
        #Start booking process. This reserves the site for 15 minutes
        browser.find_element_by_xpath('//*[@id="btnbookdates"]').click()
        pop_up()
        browser.find_element_by_xpath('//*[@id="AemailGroup_1733152645"]').send_keys(recreation_email)
        browser.find_element_by_xpath('//*[@id="ApasswrdGroup_704558654"]').send_keys(recreation_password)
        browser.find_element_by_name('submitForm').click()
        browser.find_element_by_xpath('//*[@id="equip"]').click()
        if sites[chosen_site].site_type == "RV NONELECTRIC":
            browser.find_element_by_xpath('//*[@id="equip"]').send_keys('car')
            browser.find_element_by_xpath('//*[@id="reservedetail"]/div/div[4]/div/h3').click()
            browser.find_element_by_xpath('//*[@id="vehicleLength"]').click()
            browser.find_element_by_xpath('//*[@id="vehicleLength"]').send_keys('16')
        else:
            browser.find_element_by_xpath('//*[@id="equip"]').send_keys('tent')
        browser.find_element_by_xpath('//*[@id="numoccupants"]').click()
        browser.find_element_by_xpath('//*[@id="numoccupants"]').send_keys('6')
        browser.find_element_by_xpath('//*[@id="numvehicles"]').click()
        browser.find_element_by_xpath('//*[@id="numvehicles"]').send_keys('2')
        browser.find_element_by_xpath('//*[@id="agreement"]').click()
        browser.find_element_by_xpath('//*[@id="continueshop"]').click()
        #At this point the campsite will be in the shopping cart

        #Send text message with all included info
        email_subject = arrival_date + ' to ' + depart_date
        email_toaddrs  = verizon_phone_address
        check_number = str(random.randint(0,9999)).zfill(4)
        email_body = sites[chosen_site].campground + ' ' + sites[chosen_site].site_number + '\n' + sites[chosen_site].site_type + '\nMax People: ' + sites[chosen_site].max_people + '\nRespond "Book ' + check_number + '" to book'
        if sites[chosen_site].handicapped:
            email_body = 'Handicapped Site\n' + email_body
        print "Sending email..."
        send_email(email_toaddrs, email_subject, email_body)

        #Repeatedly check email for 12 minutes
        start_time = datetime.datetime.now()
        time_elapsed = datetime.datetime.now() - start_time
        email_from, email_subject2, email_time = read_email()
        while ((not check_email_valid(email_from, email_subject2, email_time, check_number)) and (time_elapsed.total_seconds() < 720)):
            email_from, email_subject2, email_time = read_email()
            time_elapsed = datetime.datetime.now() - start_time
            print time_elapsed.total_seconds()

        if time_elapsed.total_seconds() >= 720:
            print "No valid text received. Canceling"
            browser.find_element_by_xpath('//*[@id="abandoncart"]').click()
        else:
            print "Valid text received. Booking site!"

            #This code books the campsite
            browser.find_element_by_xpath('//*[@id="chkout"]').click()
            browser.find_element_by_xpath('//*[@id="cardTypeId_1"]').click()
            browser.find_element_by_xpath('//*[@id="cardTypeId_1"]').send_keys('v')
            browser.find_element_by_xpath('//*[@id="cardnum_1"]').click()
            browser.find_element_by_xpath('//*[@id="cardnum_1"]').send_keys(credit_card_number)
            browser.find_element_by_xpath('//*[@id="seccode_1"]').click()
            browser.find_element_by_xpath('//*[@id="seccode_1"]').send_keys(security_code)
            browser.find_element_by_xpath('//*[@id="expmonth_1"]').click()
            browser.find_element_by_xpath('//*[@id="expmonth_1"]').send_keys(expire_month)
            browser.find_element_by_xpath('//*[@id="expyear_1"]').click()
            browser.find_element_by_xpath('//*[@id="expyear_1"]').send_keys(expire_year)
            browser.find_element_by_xpath('//*[@id="fname_1"]').click()
            browser.find_element_by_xpath('//*[@id="fname_1"]').send_keys(first_name)
            browser.find_element_by_xpath('//*[@id="lname_1"]').click()
            browser.find_element_by_xpath('//*[@id="lname_1"]').send_keys(last_name)
            browser.find_element_by_xpath('//*[@id="ackacc"]').click()
            browser.find_element_by_xpath('//*[@id="chkout"]').click()
            
    else:
        print "No Campsites Available!"


    browser.quit()
