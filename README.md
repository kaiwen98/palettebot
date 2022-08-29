# Palette Bot

This repository contains code contribute by NUSCAS Palette Members. 

The project encompasses a Discord Bot which currently supports the following features:

<table>

<tr>
    <th>Feature</th>
    <th>Description</th>
</tr>

<tr>
    <td>Birthday Tracker</td>
    <td>
        From an excel sheet on Google Drive, tracks birthday dates and reminds the Discord channel when a date corresponds with a member's birthdate. 
    </td>
</tr>

<tr>
    <td>Artwork Image Dumper</td>
    <td>
        From an excel sheet on Google Drive, tracks artwork permissions and dumps artworks from a selected Discord Channel.
    </td>
</tr>

<tr>
    <td>Inktober Tracker</td>
    <td>
        Runs the Inktober minigame for one month.
    </td>
</tr>

<tr>
    <td>Waifu War Tracker</td>
    <td>
        Work in progress. Tracks scores for Waifu Wars.
    </td>
</tr>

</table>

## Recommended prerequisites
1. Basic Command Line interface
1. Version control with Git and Github
1. Discord Library for Python (Google as you go)
1. Python Pandas    

## Resources to Learn
1. [Kaggle Courses](https://www.kaggle.com/) 
    1. Python
    1. Pandas

1. [Discord Bot Tutorial](https://realpython.com/how-to-make-a-discord-bot-python/)

1. [Discord Bot Documentation](https://discordpy.readthedocs.io/en/stable/api.html)
    * You don't need to know everything. Just look up what you happen to need to know.

1. [Software Engineering @ CS2113/T](https://nus-cs2113-ay2122s1.github.io/website/) 
    1. Good place to learn version control
    1. Learn about Forking Workflow

1. [Google Service API Auth](https://d35mpxyw7m7k7g.cloudfront.net/bigdata_1/Get+Authentication+for+Google+Service+API+.pdf)

1. Stack Overflow. Seriously.


## Set-up 
1. Install Python 3.9.5 as well as Pip.
1. Install Git.
1. Download an IDE. VSCode is the recommended IDE for this project. You can also look at Pycharm or Sublime.
1. Fork the repository to your own repository.
1. Open up a new command terminal.
1. Clone the repository to your local directory.
    * ```git clone https://github.com/yourname/palettebot.git```
1. Set up a python virtual environment. 
    * ```python -m venv env```
1. Start your python virtual environment.
    * ```env\Scripts\activate.bat```
1. Run pip install
    * ```pip install -r requirements.txt```
1. Run the script and verify that it works.
    * ```python app.py```

## Directory overview
1. ```Procfile```, ```runtime.txt```
    * Heroku files. Heroku is a cloud service that we use to run the script 24/7. This means no one needs to leave their computer on forever.
1. ```config_loader.py```
    * If script is run from Heroku, then use actual channels for input and output. (#art-gallery, #general)
    * Else if script is run from a PC (local environment), then use test channels. (#bot-spam, #exco-chat)

1. ```controller/```
    * Main folder for files encompassing feature logic

1. ```io/```
    * Main folder for image files, or any other output artifacts that are not required in feature logic

1. ```utils/```
    * If alot of features use the same function, then consolidate in this folder.

1. ```.gitignore```
    * Some features require automated access to Google Sheet and stuff. 
    * Since they are mostly sensitive data, we need to protect it with credentials.
    * Instead of a login page, verifying credentials in code is provision of a certain file, for instance
    ```credentials.json```
    * We want our keys in our own pockets (local directory), but we don't wnat them on some random garden bench (Github repository)
    * This file is to tell Github which files to not put onto this garden bench. 

1. ```requirements.txt```
    * To do cooler stuff in python, you need to use other people's code to build your own code. We call them libraries.
    * This file contains all libraries that a new developer must download so that the code has what it needs to run.

