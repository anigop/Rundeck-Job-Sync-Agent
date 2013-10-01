'''
Created on Jul 18, 2013

@author: agopalakrishnan
'''

import requests
from xml.dom import minidom
import xml.etree.ElementTree as ET
import urllib
import json 
from optparse import OptionParser
import sys
'''
Read configuration file
'''


class credentials:
    def __init__(self,api_key,server_name):
		self.api_key = api_key
		self.server_name = server_name

class job:
	def __init__(self,job_id,job_name):
		self.job_id = job_id
		self.job_name = job_name

class server:
	def __init__(self,server_id,server_name,api_key):
		self.server_id = server_id
		self.server_name = server_name
		self.api_key = api_key

def searchTag(root,target,path):
    if root.tag is None:
        return None
    if root.tag == target:
        return path+""+target
    for child in root:
        str = searchTag(child,target,path+""+root.tag+"/")
        if not str is None:
            return str
    return    

def read_servers(filename):
	#print("Reading server file")
	server_list = []
	conf_handler = open(filename,"r")
	json_stream = conf_handler.read()
	json_object = json.loads(json_stream)
	for serv in json_object["servers"]:
		oServer  = server(serv["id"],serv["name"],serv["api_key"])
		server_list.append(oServer)
	return server_list


def readConfig(filename):
	conf_handler = open(filename,"r")
	json_stream = conf_handler.read()
	json_object = json.loads(json_stream)
	server_name = json_object['server_name']
	api_key = json_object['api_key']
	creds = credentials(api_key,server_name)
	return creds
	
def pullJobs(api_key,project,server_url):
	headers = {"X-Rundeck-Auth-Token":api_key}
	queryString = server_url+"/api/2/project/"+project+"/jobs"
	response = requests.get(queryString,headers=headers)
	resp_string = check_response(response)
	
	if resp_string == "OK":	
		xml_tree = ET.fromstring(response.text)
		
		joblist = xml_tree.findall('./jobs/job')
		
		if len(joblist) == 0:
			print(" No jobs found for this project")
		else:
			job_map = {}
		        #print(response.text)	
			for jobs in joblist:
				job_map[jobs.find('name').text.replace(" ","")] = jobs.get('id')	 	 
			return job_map
	else:
		print(resp_string)	
		return None

def download_job(api_key,job_name,job_id,server_url):
	headers = {"X-Rundeck-Auth-Token":api_key}
	query_string = server_url+"/api/1/job/"+job_id
	
	response = requests.get(query_string,headers=headers)
	resp_string = check_response(response)
	
	if resp_string == "OK":
		xml_tree = ET.fromstring(response.text)
		
		#print(response.text)
		job_file_write_handler = open(job_name+".xml","w")
		job_file_write_handler.write(response.text)
	else:
		print(resp_string)	

def download_jobs(api_key,job_map,server_url):
	for job_n , job_id in job_map.iteritems():
		download_job(api_key,job_n.replace(" ",""),job_id,server_url)

def pull(creds,job_map,job_name):
	if not job_map is None:
                for job_n , job_id in job_map.iteritems():
                        print(job_n+"--"+job_id)
	else:
                print("Unsuccessful list call..exitting")
                sys.exit()

	if not job_name == "all":
                newmap = {}
                if job_name.replace(" ","") in job_map:
                        newmap[job_name] = job_map[job_name]
                        download_jobs(creds.api_key,newmap,creds.server_name)
                else:
                        print("No such job in project")
	else:
                download_jobs(creds.api_key,job_map,creds.server_name)

'''
Check the response received after the rest API so that error can be raised accordingly
'''	

def check_response(response):
	if response.status_code == 403:
                return "Invalid API Key, please check your api key and server name"
	elif response.status_code == 404:
                return "Error code :  404, please check the project name and retry"
	elif response.status_code == 405:
                return " Error code : 405 - Method not allowed"
	else:
		return "OK"

'''
 This method process that HUUUGe string that is passed in to edit the file in
 this format  <tag>=<value>::<tag>=<values> --- a=b::v=x,y,z 
'''

def process_params(params):
	key_pair_list = params.split("::")
	attribute_map = {}
	for key_pair in key_pair_list:
		pair_tokens = key_pair.split("=")
		if len(pair_tokens) == 2: 
			attribute_map[pair_tokens[0]] = pair_tokens[1]
		else:
			print("Attributes were not in the right format, please enter a valid format")
			return None

	return attribute_map



def modify_files(filename,params,output_file):
	attribute_map = process_params(params)

#	print(attribute_map)	

	if not attribute_map is None:
		print("Reading job desc from file - "+filename)
		try:
			file_handler  = open(filename,"r")
			raw_string = file_handler.read()
                                #print(xml_string)
			xml_tree = ET.fromstring(raw_string)
		except IOError:
                	print("Error Reading file")
	
		for key,value in attribute_map.iteritems():
			#print("Modifying tag "+key+" with value= "+value)
			#print("Reading job desc from file - "+filename)
			
			try:
				file_handler  = open(filename,"r")
				raw_string = file_handler.read()
				#print(xml_string)
				
				#xml_tree = ET.fromstring(raw_string)
				
				if not key.find("#") == -1:
					key_token = key.split("#")
					if  len(key_token) ==  2:
						tag_path = searchTag(xml_tree,key_token[0],"")
						
						if tag_path is None:
							print("Could not find tag -"+key+"... skipping")
						else:
							tokens = tag_path.split("/")
							path_to_name = "."+tag_path[tag_path.index("/"):]
							print("Found path at "+path_to_name)
							list = xml_tree.findall(path_to_name)	
							found = False							
							for tag in list:
								
								if key_token[1].find("?") is -1:
									print("No attribute parameter-value specified")
								else:
									key_attr_token = key_token[1].split("?")
									attr_value = key_attr_token[0].split(":")
									
									if len(attr_value) == 2:
										if tag.get(attr_value[0]) == attr_value[1] and not tag.get(attr_value[0]) is None:
											key_to_set = key_attr_token[1].split("=")
											found = True
											if  len(key_to_set) >= 2:
												print("Invalid format specification for tag attribute modification")
											else:
												if tag.get(key_to_set[0]) is None:
													print("No such attribute "+key_to_set[0]+" in tag")
												else:
													tag.set(key_to_set[0],value)
													print("Successfully modified "+key_to_set[0]+" to "+value) 
							if not found is True:
								print(" Attribute name provided for value check of this tag not found  "+key_token[1])

									
							
							
												
					else:
						print("Incorrect input format, mod-params will have exactly  one # per key")
				else:
					tag_path = searchTag(xml_tree,key,"")
				
					if tag_path is None:
						print("Could not find tag -"+key+"... skipping")
					else:
						tokens = tag_path.split("/")
					
						path_to_name = "."+tag_path[tag_path.index("/"):]
						print("Found path at "+path_to_name)
					
						list = xml_tree.findall(path_to_name)
						for tags in list:
							print(" Value set for "+tags.text+" with "+value)
							tags.text = value
				
				
				output_file_handler = open(output_file,"w")
				output_file_handler.write(ET.tostring(xml_tree))
				print("Created output file "+output_file+" with updated values")		
			except IOError:
				print("IO Error")
		
		'''
		Creating output for the modified job def file
		'''	
				

	else:
		print("Something went wrong while reading attribute values") 

def push(api_key,server_name,xml_file,dup_type):
    file_handle = open(xml_file,"r")
    xml_batch_content = file_handle.read()
    headers = {"X-Rundeck-Auth-Token":api_key}

    upload_url_prefix = server_name+"/api/1/jobs/import"

    print("Uploading  "+xml_file+"...")
    
    params ={"xmlBatch":xml_batch_content,"dupeOption":dup_type}
    r = requests.post(upload_url_prefix,data=params,headers=headers)
    
    if r.status_code == 200:
        print(" Job def "+xml_file+"  successfully uploaded")
    else:
        print(" Job def "+xml_file+" could not be uploaded, status code  "+r.status_code)
   
def main():
	#config_file_name = "rundeck-cli.conf"

	parser = OptionParser()
	parser.add_option("--conf-file", action = "store",dest ="conf", default="--", help = "Please provide a configuration file location")
	parser.add_option("--push", action = "store_true",dest ="mode_push", default=False, help = "Use this flag to push jobs to the server")
	parser.add_option("--pull", action = "store_true",dest ="mode_pull", default=False, help = "Use this flag to pull jobs from the server")
	parser.add_option("--project",action ="store", dest="project",default ="--",help = "Enter a valid project name on the rundeck server")	
	parser.add_option("--job", action="store",dest = "job_name",default = "--",help = "Enter a valid jobname on the server")
	parser.add_option("--job-list",action="store_true",dest= "list_flag",default = False, help = "Set this flag to list all jobnames for the project")
	parser.add_option("--modify",action="store_true",dest="modify",default=False, help = "Use this flag to edit xml files")
	parser.add_option("--push-to",action = "store",dest="dest_server",default="--",help = "Use this file to specify which server to be pushed to")
	parser.add_option("--mod-params",action="store",dest="mod_params",default="--", help="Use this flag to pass in tags and values that have to be modified <tag>=<value>::<tag#key:value?attr=values> --- a=b::w#v:t?g=x,y,z")
	parser.add_option("--file",action="store",dest="target_file",default="--",help="Provide file path that is to be pushed or modified")
	parser.add_option("--output-file",action="store",dest="output_file",default="--",help="Provide output file name for pull or modify mode")
	parser.add_option("--push-mode",action="store",dest="push_mode",default="update",help="specify mode in which it the job has to be pushed")

	(options,args) = parser.parse_args()
	
	if options.mode_push is False and options.mode_pull is False and options.modify is False:
		print("Specify a mode this script has to run on, either push,pull or modify")
		sys.exit()
	
	if options.conf is "--":
		print("Please provide a valid configuration file path")
		sys.exit()

	config_file_name = options.conf
	creds = readConfig(config_file_name)
	
	if options.project is "--":
		print("Please enter a valid project name")
		sys.exit()
	project = options.project
    
	if options.list_flag is True:
		job_map = pullJobs(creds.api_key,options.project,creds.server_name)
		if not job_map is None:
			for job_n , job_id in job_map.iteritems():
				print(job_n+"                                                           "+job_id)
    	sys.exit()
    	
	if options.job_name is "--":
		print("Please enter a valid job name") 
		sys.exit()
	
	if options.mode_push is True and options.mode_pull is True and options.modify is True:
		print("Please specify one mode")
		sys.exit()	
  	
	elif options.mode_push is True and options.mode_pull is True:
		print("Script cannot run in both push and pull modes")
		sys.exit()

#	elif options.mode_push is False and options.mode_pull is False:
#		print(" Please specify a mode (push or pull) ")
#		sys.exit()
	
	elif options.mode_pull is True:
		mode = "PULL"
		project = options.project

		job_map = pullJobs(creds.api_key,options.project,creds.server_name)
		pull(creds,job_map,options.job_name)
	elif options.mode_push is True:
		mode = "PUSH"
		print("Running Push mode")
		server_list = read_servers("rundeck-serverinfo.conf")
		#print("length of server conf")
		#print(len(server_list))
		otarget_server_list = [target for target in server_list if target.server_id == options.dest_server]
		if otarget_server_list is None:
			print("No server with specified ID was found in server_info file")
		else:
			if len(otarget_server_list) < 1:
				print("Could not find server with that ID, please check the rundeck-serverInfo file and try again")
			else:
				otarget_server = otarget_server_list[0]
				#print("server was found"+otarget_server.server_id+"  "+options.dest_server)
				if options.target_file == "--":
					print("Please enter a job definition file that should be pushed")
				else:
					if options.push_mode == "update" or options.push_mode == "create" or options.push_mode == "skip":
						push(otarget_server.api_key,otarget_server.server_name,options.target_file,options.push_mode)
					else:
						print(" Please enter a valid push mode \"update\" , \"create\" , \"skip\"")
	else:
		mode = "MODIFY"
		if options.target_file is "--":
			print("Please provide a filename that is to be modified")
		else:
			modify_files(options.target_file,options.mod_params,options.output_file)

		

if __name__=='__main__':
	main()
