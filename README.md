This project contains some support tools for the Twin Pigs Agile process. It's an Excel table template, an Excel script file, and a Python proxy integrating the Excel scripts with Jira API. If you need other integrations, you may implement them yourself.
# Welcome to the Twin Pigs Agile Process

**The Twin Pigs Agile process** is a flexible Agile process suggesting a highly customisable approach to organising work of multiple teams. The **twinpigs-excel** project is a simple tool to support Twin Pigs sprint planning in Excel. Currently, the project contains the following:

 - An Excel file (`excel/TwinPigs.xlsx`). Initially, it contains a single worksheet which you may customise and clone later. Just do not forget to set up the Excel script (described below).
 - A TypeScript Excel script `excel/scripts/twinpigs-excel.ts`. You should create a new script using *Automate* menu in Excel and open it for editing. Then copy-paste the script body there and save the file. The **...** menu in the upper right corner of the editor allows you to *Add in workbook*. That creates a button. Delete the old **Run** button and replace it with the new one. Edit its caption to say **Run** and save the file.
 - A Python script `jiraproxy.py`. It allows you to integrate your Excel file with Jira. The latest executable is available in the **Releases** section of the repository. Or you may run it as a Python script (just install the dependencies from `requirements.txt`). Two parameters are required: the Jira URL (e.g., `--jira=https://myjira.example.com:8080`) and a Jira Personal Access Token (e.g., `--jira=821734897623ujyg4y2u13`). It's recommended to leave the default values of other parameters. The proxy should always be run when (and only when) you exchange data with Jira.

