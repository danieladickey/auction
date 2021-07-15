# README - PROJECT WHISKERS

## Explanation of the Organization and Name Scheme for the Workspace
Project is divided into classes following standard naming protocol. CamelCase will be used in lieu of the less desirable under_Score method when namind variables and objects.

## Version Control Procedures
Use a separate branch for every task you work on. Do not review your own code. Delete branches after merge.(Scrum Lord exempt)

## Tool Stack Description and Setup Procedure
We will use Anaconda to ensure all team members are using the same software and tools. We will all use Pycharm as the IDE. 

* Python 3.7.4
* Anaconda 4.7.12
* Django 2.2.1

## Build Instructions
0. Install Anaconda
1. Install Django
2. Using the Anaconda Prompt, from within the ".../src/ProjectWhiskers" directory run "python manage.py runserver 0.0.0.0:80" 
3. From the command prompt, run "ipconfig" to find your IP address which should look something like: 144.39.239.89
4. Open your favorite Web Browser and navigate to your IP address, this should work from any device connected to the same network.

## Unit Testing Instructions
0. Using the Anaconda Prompt, from within the ".../src/ProjectWhiskers" directory run "python manage.py test auction" 

## System Testing Instructions
To populate database with test data, run:

'''python manage.py makemigrations'''

'''python manage.py migrate'''

'''python manage.py populate'''


To tear down database, run:
'''python manage.py reset'''

To tear down and populate the database, run:
'''python manage.py fullRestart'''

## System Testing Instructions
0. Using the Anaconda Prompt, from within the "src/ProjectWhiskers" directory run "python manage.py test auction" 

## Notes
See Glossary for more info on Scrum Lord.
# Auction
