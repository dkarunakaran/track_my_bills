from download import Download
from generate import Generate

def run():
    download = Download()
    generate = Generate()

    # Read and process emails - Action 1
    download.get_emails()

    # Read and check bank details. This is to make sure the bank details has not been changed - Action 2
    # If there is any change to bank details, wait for the human to proceed to update the bank details, otherwise continute to action 3
    
    # Read and process drive files - Action 3
    download.get_drive_files()

    # Read and check bank details. This is to make sure the bank details has not been changed - Action 4
    # If there is any change to bank details, wait for the human to proceed to update the bank details, otherwise continute to action 5

    # Create the Task based on the processed data - Action 5
    generate.task_API_operation()



if __name__ == '__main__':
    run()