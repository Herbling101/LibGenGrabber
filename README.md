# LibGenGrabber.py
A simple CLI for downloading scientific papers through libgen

-Allows you to query LibGen (even with advanced search)
-Returns all results from the query, with associated paper titles, publication date, and download link
-creates a folder for each query in your working directory, and downloads all results to the folder
-(Optional) uses multi-threading to speed up downloads
-Automatic file-naming (names files by title of paper)


#Usage
This is not yet installable as a package, and it does not have a requirements.txt file.
You will have to view the imports at the top of the script and pip install them if they are not already in your python environment.
For now, it is intended to just run as a script to initialize a command-line-interface through which its functionality can be utilized

Personally
-I have this file saved in a "Scripts" folder, and I have a function on my bash.bashrc file to run the script when I type a keyword.
-This will run the CLI in whatever working-directory I opened my shell in. The folders created, which contain the downloaded files, will be in this working-directory.


If you like it or have any suggestions or questions, please reach out!
