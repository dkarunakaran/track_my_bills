from download import Download
from generate import Generate

def run():
    download = Download()
    generate = Generate()

    # Read and process emails
    download.get_emails()
    
    # Read and process drive files 
    download.get_drive_files()

    # Create the Task based on the processed data 
    generate.task_API_operation()



if __name__ == '__main__':
    run()