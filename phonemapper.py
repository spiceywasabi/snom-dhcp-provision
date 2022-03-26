#!/usr/bin/env python3

import jinja2
import os
import sys
import csv
import uuid
import logging
import logging.handlers
from pprint import pprint



# init logging
Log_Format = "%(levelname)s %(asctime)s - %(message)s"

logging.basicConfig(
					#filename = "phonemapper.log",
                    stream = sys.stdout, 
                    filemode = "w",
                    format = Log_Format, 
                    level = logging.DEBUG)

phonelog = logging.getLogger()
#handler = logging.handlers.SysLogHandler(address = '/dev/log')
#phonelog.addHandler(handler)


OUTPUT_FILENAMES = [
	"/var/www/html/{{ mac }}.htm",
	"/var/www/html/{{ mac}}.xml",
	"/var/www/html/{{ model }}-{{ mac }}.htm",
	"/var/www/html/{{ model }}-{{ mac }}.xml",
	"/var/tftpd/{{ mac }}.htm",
	"/var/tftpd/{{ mac }}.xml",
	"/var/tftpd/{{ model }}-{{ mac }}.htm",
	"/var/tftpd/{{ model }}-{{ mac }}.xml"
	]

"""

OUTPUT_FILENAMES = [
	"./test.xml",
	]

team_phone_name 
 team_admin_username 
 team_admin_password 
 team_idx1_display_name 
 team_idx1_account 
 team_idx1_password 
 team_idx1_uuid 
 team_idx1_ringer 
 team_idx1_ringer_url 
 team_idx2_display_name 
 team_idx2_account 
 
 team_idx2_password 
 team_idx2_uuid 
 team_idx2_ringer 
 team_idx2_ringer_url 
"""

# fixed config mostly here
sip_server="REPLACEME"
syslog_server="REPLACEME"

phone_mapping = "./SIPPassList.csv"
phone_address_book = "./phonebook.csv"
 

templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
XML_TEMPLATE_FILE = "phone.xml.j2"
MODEL="VTechET605" # need a model or list of models ???

dhcpaction = 'unknown'

if not os.path.exists(phone_mapping):
	phonelog.error(f"could not find phone mapping file: '{phone_mapping}'.")
	sys.exit(1)

if not os.path.exists(phone_address_book):
	phonelog.warning(f"couldn't find address book ('{phone_address_book}'), skipped")

if len(sys.argv) > 1:
	dhcpaction = str(sys.argv[1])
	phonelog.debug(f"detected new message from dhcp server with action: '{dhcpaction}'")

with open(phone_mapping, newline='') as phonemap:
	reader = csv.DictReader(phonemap)
	for row in reader:
		try:
			phonelog.info(f"Reading Config for Phone: {row['user']}")
			mac = str(row['mac']).strip().upper()
			raw_name = row['user'].replace(" ","")
			phone_name = f"phone-{raw_name}-{mac}".replace(":","").lower()
			admin_pass = str(row['admin_password']).lower()
			phone_model = PHONE_MODEL
			
			phonelog.info(f"Phone Found: {mac} with name {phone_name}")
		
			# set boot lock just in case
			boot_lock = None
			if row['boot_lock'].strip() != "" and row['boot_lock'] != "FALSE":
				boot_lock = str(row['boot_lock']).strip() 
		
			team_line1_display_name  = None
			team_line1_account = None
			team_line1_password  = None
			team_line1_ringer  = "Custom" # None
			team_line1_ringer_url  = custom_ringtone
			team_line2_display_name  = None
			team_line2_account = None
			team_line2_password  = None
			team_line2_ringer  = custom_ringtone
			team_line2_ringer_url  = None

			# EXT 1
			if "line1_name" in row:
				team_line1_display_name  = str(row['line1_name'])
			if "line1_extension" in row:
				team_line1_account = str(row['line1_extension'])
			if "line1_secret" in row:
				team_line1_password  = str(row['line1_secret']).strip()
			if "line1_ringer" in row:
				team_line1_ringer  = str(row['line1_ringer']).strip()
			if "line1_ringer_url" in row:
				team_line1_ringer_url =  str(row['line1_ringer']).strip()
			else:
				team_line1_ringer_url  = custom_ringtone
			team_line1_uuid  = str(uuid.uuid4())
			# EXT 2
			if "line2_name" in row:
				team_line2_display_name  = str(row['line2_name'])
			if "line2_extension" in row:
				team_line2_account = str(row['line2_extension'])
			if "line2_secret" in row:
				team_line2_password  = str(row['line2_secret']).strip()
			if "line2_ringer" in row:
				team_line2_ringer = str(row['line2_ringer']).strip()
			if "line2_ringer_url" in row:
				team_line2_ringer_url  = str(row['line2_ringer']).strip()
			#else:
			#	team_line2_ringer_url  = custom_ringtone
			team_line2_uuid  = str(uuid.uuid4())
			
			# now the extensions 
			if "line1_extension" in row:
				phonelog.debug(f"Found Extension Line: 1 EXT - x{str(row['line1_extension'])} ")
			if "line2_extension" in row:
				phonelog.debug(f"Found Extension Line: 2 EXT - x{str(row['line2_extension'])} ")

			# now we have all the info we try to load the phone book
			has_phonebook = False
			contacts = None
			if os.path.exists(phone_address_book):
				phonelog.info(f"Starting phone book builder")
				has_phonebook = True
				with open(phone_address_book, newline='') as phonebook:
					book_reader = csv.DictReader(phonebook)
					contacts = []
					for book_row in book_reader:
						if 'number' in book_row:
							numbr = book_row['number']
							name = book_row['name']
							phonelog.info(f"Adding phone book entry {name} with num {numbr}")
							contacts.append({
								'number': numbr,
								'name': name,
								'type': 'sip'
							})
						else:
							phonelog.error(f"Invalid Phone Book Line: {book_row}")
			# lol 
			template = templateEnv.get_template(XML_TEMPLATE_FILE)
			outputText = template.render(
				sip_server = sip_server,
				syslog_server = syslog_server,
				team_admin_password = admin_pass,
				team_admin_username = 'admin',
				team_idx1_account = team_line1_account,
				team_idx1_display_name = team_line1_display_name,
				team_idx1_password = team_line1_password,
				team_idx1_ringer = team_line1_ringer,
				team_idx1_ringer_url = team_line1_ringer_url,
				team_idx1_uuid = team_line1_uuid,
				team_idx2_account = team_line2_account,
				team_idx2_display_name = team_line2_display_name,
				team_idx2_password = team_line2_password,
				team_idx2_ringer = team_line2_ringer,
				team_idx2_ringer_url = team_line2_ringer_url,
				team_idx2_uuid = team_line2_uuid,
				team_phone_name = phone_name,
				uboot_lock = boot_lock,
				phonebook_defined = has_phonebook,
				phonebook = contacts
			)
			# lol2
			for OUTPUT_FILENAME in OUTPUT_FILENAMES:
				fn = jinja2.Template(OUTPUT_FILENAME)
				conf_file = fn.render(mac=mac,team_phone_name=phone_name,model=phone_model)
				#phonelog.info(f"Attempting to write to {conf_file}")
				with open(conf_file, 'w+') as config:
					config.write(outputText)
		except (TypeError):
			phonelog.error(f"Unable to read phone config...")	
			phonelog.debug(f"Invalid Config CSV Line: {str(row)}")
			sys.exit(1)
			# expected values:
			#mac,user,line1_extension,line1_name,line1_secret,boot_lock,admin_password



