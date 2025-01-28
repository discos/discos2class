import datetime
import glob
import os
import re
import subprocess

class FileServices():

    def __init__(self):

        pass
       
    
    def get_projects_id(self, root_folder):

        projects_id = []

        # Typically, the projects ID have the following pattern '##-##' or '#-##'
        # The relative regular expression (RegEx) is the following:
        r = re.compile("^[0-9]{1,2}-[0-9]{2}$")

        # At first, check if a specific directory or mount point exists
        print(os.path.exists(root_folder))

        if os.path.ismount(root_folder):
    
            print(f"Disk {root_folder} is mounted and visible.")

            try:

                tmp_subfolders = os.listdir(root_folder)

            except:

                pass
          
            else:

                for i in range(len(tmp_subfolders)):
                    # Check if the file is a an existing directory
                    if os.path.isdir(root_folder + tmp_subfolders[i]):
                        # Check if the folder matches the RegEx
                        if r.match(tmp_subfolders[i]) is not None:
                        
                            projects_id.append(tmp_subfolders[i])
        
        else:
            
            print(f"Disk {root_folder} is not mounted or not visible.")

    
        return projects_id


    def get_folders(self, folder, folder_level):

        # Each folder level related to a combo box has its own filtering rules to get the folders
        folders = []

        try:
        
            tmp_subfolders = os.listdir(folder)
        
        except:
            
            pass

        else:

            # Level 0 folders have the format YYYYmmdd
            if(folder_level=="0-sl"):

                for i in range(len(tmp_subfolders)):
                    # Add only folders 
                    if os.path.isdir(folder+"/"+tmp_subfolders[i]):
                        # check the format
                        try:
                            
                            datetime.datetime.strptime(tmp_subfolders[i], "%Y%m%d")
                            folders.append(tmp_subfolders[i])

                        except ValueError:
                            
                            pass
                            # print("Date invalid")

            # Level 1 folders must contain:
            # Sum*.fits file
            # "tmp" folder (check if "tempfits" folder is also present for Sardara AND Skarab) 
            # More than one .fits file (one is already related to the Sum*.fits file) [len(*.fits) > 1] 
            if(folder_level=="1-sl"):

                for i in range(len(tmp_subfolders)):
                    # Perform the file and folders check  
                    if (os.path.isdir(folder+"/"+tmp_subfolders[i])):
                        
                        if (os.path.isdir(folder+"/"+tmp_subfolders[i]+"/"+"tmp")):
                          
                            # Fastest method to retrieve all files in a folder with a given extention
                            count = 0
                            # Iterate over files in the directory using os.scandir (faster than os.listdir)
                            with os.scandir(folder+"/"+tmp_subfolders[i]) as entries:
                                
                                #print(folder+"/"+tmp_subfolders[i])
                                for entry in entries:
                                    
                                    if entry.is_file() and entry.name.endswith('.fits'):
                                        count += 1

                            summary_fits_file = glob.glob1(folder+"/"+tmp_subfolders[i], "Sum_*.fits")


                            if(count > 1 and summary_fits_file != ""):

                                folders.append(tmp_subfolders[i])
        
        return folders

    
    def ping_server(self, remote_ip):

        # Example usage from external class
        # remote_ip = "192.168.1.100"  # Replace with the server IP address
        # ping_server(remote_ip)
        
        try:
            response = subprocess.run(
                ["ping", "-c", "1", remote_ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            if response.returncode == 0:
                
                print(f"Server {remote_ip} is reachable.")
                return True
            
            else:
                
                print(f"Server {remote_ip} is not reachable.")
                return False
        
        except Exception as e:
            
            print(f"Error pinging server: {e}")
            return False