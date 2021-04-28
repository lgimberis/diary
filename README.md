## Disclaimer
__THIS PROGRAM IS IN DEVELOPMENT.
THIS PROGRAM MAY PERMANENTLY DELETE FILES FROM YOUR COMPUTER.
I ACCEPT NO RESPONSIBILITY FOR THIS.
I DO NOT RECOMMEND ANYONE USE THIS IN ITS CURRENT STATE UNLESS THEY'RE REALLY SURE WHAT THEY'RE DOING.
YOU HAVE BEEN WARNED.__

## Summary
CLIDiary (Command Line Interface Diary) is a program that keeps an encrypted, password-protected database of text files.
As the name suggests it provides a CLI for interacting with its contents.
Whenever files are not actively being edited, they will be encrypted.

## Usage
To use CLIDiary, run the CLI via the following command from the directory that contains the clidiary module:
`python -m clidiary.main [path]`
where path is an optional argument containing the database root directory,
using the current directory if not provided.

## Using the CLI
To use the CLI, the two main commands you should be aware of are "help" and "exit", which function as their name implies.
Apart from this, notably the intended use case of this program is to bring up a file specific to the current day, for which the command "today" is provided.

## Regarding text editors
CLIDiary will by default launch text files in the system default text editor.
If this is an editor such as notepad++ which opens a new tab instead of a new session for each file, this program may not work properly.
It is necessary to either force the editor to use one tab per session in the editor's settings, or to close the editor between opening each file.

## Writing to CLIDiary
Text files sent to CLIDiary currently require a special format.
This format supports categories and subcategories, denoted by enclosure in square brackets '[]' and parentheses '()' respectively.
Categories are mandatory. Subcategories are optional.
Example:

[My Category]
I am writing about the subject of My Category without any particular subcategory.
(My Sub-category)
I am writing about this subcategory. In future, I will be able to find this particular text snippet by searching for both My Category and My Sub-category.
